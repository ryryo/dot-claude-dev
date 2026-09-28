#!/usr/bin/env python3
"""Resumable local MLX ASR. Requires ffmpeg, ffprobe and mlx-whisper."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile


def save(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def normalized(parts):
    segments, adjusted = [], 0
    for part in parts:
        offset, duration = part['offset_seconds'], part['duration_seconds']
        for segment in part['raw'].get('segments', []):
            start, end = float(segment['start']), float(segment['end'])
            if not math.isfinite(start) or not math.isfinite(end) or end <= start or end <= 0 or start >= duration:
                adjusted += 1
                continue
            clipped_start, clipped_end = max(0, start), min(duration, end)
            adjusted += int((clipped_start, clipped_end) != (start, end))
            segments.append({'start': offset + clipped_start, 'end': offset + clipped_end,
                             'text': segment['text'].strip(), 'part': part['index']})
    return {'segments': segments, 'adjusted_or_excluded_segments': adjusted,
            'timing_note': 'Approximate ASR times, clipped to each chunk; raw outputs preserved.'}


def timestamp(seconds):
    seconds = int(seconds)
    return f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--model', default='mlx-community/whisper-large-v3-turbo')
    parser.add_argument('--language', default='ja', help='Language code, or auto')
    parser.add_argument('--chunk-seconds', type=float, default=480)
    parser.add_argument('--allow-download', action='store_true')
    args = parser.parse_args()
    if not math.isfinite(args.chunk_seconds) or args.chunk_seconds <= 0:
        parser.error('--chunk-seconds must be finite and positive')
    source = args.source.expanduser().resolve(strict=True)
    output = args.out.expanduser().resolve()
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(source)]))
    if not any(s['codec_type'] == 'audio' for s in probe['streams']):
        parser.error('No audio stream; use visual analysis, not fabricated speech.')
    duration = float(probe['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        parser.error('Source duration is invalid')
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if not args.allow_download:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
    version = importlib.metadata.version('mlx-whisper')
    config = {'source_sha256': digest.hexdigest(), 'duration_seconds': duration,
              'model': args.model, 'language': args.language, 'chunk_seconds': args.chunk_seconds,
              'engine': 'mlx-whisper', 'version': version, 'schema_version': 1}
    output.mkdir(parents=True, exist_ok=True)
    manifest_file = output / 'manifest.json'
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        if manifest['config'] != config:
            parser.error('Source or recognition settings changed; choose a new --out directory.')
    else:
        if any(output.iterdir()):
            parser.error('Output is not empty and has no matching manifest; choose a new --out.')
        manifest = {'config': config, 'source_path': str(source), 'status': 'in_progress', 'completed_parts': []}
        save(manifest_file, manifest)
    import mlx_whisper
    parts = []
    count = math.ceil(duration / args.chunk_seconds)
    for index in range(count):
        offset = index * args.chunk_seconds
        length = min(args.chunk_seconds, duration - offset)
        part_file = output / f'part-{index + 1:04d}.json'
        if part_file.exists():
            part = json.loads(part_file.read_text(encoding='utf-8'))
            if (part['index'], part['offset_seconds'], part['duration_seconds']) != (index + 1, offset, length):
                parser.error(f'Part metadata mismatch: {part_file}')
        else:
            print(f'Transcribing {index + 1}/{count}: {offset:.2f}–{offset + length:.2f}s', flush=True)
            with tempfile.TemporaryDirectory(prefix='seminar-asr-') as temporary:
                wav = Path(temporary) / 'audio.wav'
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', str(offset),
                                '-i', str(source), '-t', str(length), '-map', '0:a:0', '-vn',
                                '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(wav)], check=True)
                raw = mlx_whisper.transcribe(str(wav), path_or_hf_repo=args.model,
                                            language=None if args.language == 'auto' else args.language,
                                            condition_on_previous_text=False, verbose=None)
            part = {'index': index + 1, 'offset_seconds': offset, 'duration_seconds': length, 'raw': raw}
            save(part_file, part)
        parts.append(part)
        manifest['completed_parts'] = [p['index'] for p in parts]
        manifest['status'] = 'in_progress'
        save(manifest_file, manifest)
    transcript = normalized(parts)
    save(output / 'transcript.json', transcript)
    (output / 'transcript.txt').write_text(''.join(
        f"[{timestamp(s['start'])}–{timestamp(s['end'])}] {s['text']}\n" for s in transcript['segments']), encoding='utf-8')
    (output / 'full-transcript.txt').write_text(''.join(
        s['text'] + '\n' for s in transcript['segments']), encoding='utf-8')
    manifest['status'] = 'complete'
    manifest['parts_total'] = count
    manifest['segments_total'] = len(transcript['segments'])
    save(manifest_file, manifest)
    print(json.dumps({'output': str(output), 'parts': count, 'segments': len(transcript['segments'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
