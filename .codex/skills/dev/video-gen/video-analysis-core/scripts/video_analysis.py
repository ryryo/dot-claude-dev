#!/usr/bin/env python3
"""Local, OCR-free visual sampling. Delivers images; does not judge their meaning."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np

VERSION = 1


def read_features(source):
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_streams',
        '-show_format', '-of', 'json', str(source)]))
    streams = probe.get('streams', [])
    if not streams:
        raise ValueError('No video stream')
    frames = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'frame=best_effort_timestamp_time', '-of', 'json', str(source)]))['frames']
    pts = np.array([float(f['best_effort_timestamp_time']) for f in frames])
    if not len(pts) or np.any(np.diff(pts) < 0):
        raise ValueError('Video requires nondecreasing frame timestamps')
    values = {key: [] for key in ('x', 'h', 'z', 'sharp', 'contrast', 'delta')}
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen([
            'ffmpeg', '-v', 'error', '-i', str(source), '-map', '0:v:0',
            '-vf', 'scale=160:96', '-fps_mode', 'passthrough', '-f', 'rawvideo',
            '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=err)
        previous = None
        try:
            while True:
                raw = proc.stdout.read(160 * 96 * 3)
                if not raw:
                    break
                if len(raw) != 160 * 96 * 3:
                    raise ValueError('Incomplete decoded frame')
                a = np.frombuffer(raw, np.uint8).reshape(96, 160, 3)
                rgb = a.astype(np.float32) / 255
                gray = rgb.mean(axis=2)
                values['x'].append(rgb.reshape(16, 6, 16, 10, 3).mean(axis=(1, 3)).ravel())
                values['h'].append(np.concatenate([
                    np.bincount((a[:, :, c] // 16).ravel(), minlength=16)
                    for c in range(3)]) / (160 * 96))
                low, high = np.quantile(gray, [.02, .98])
                normalized = np.clip((gray - low) / max(high - low, .08), 0, 1)
                values['z'].append(normalized.reshape(16, 6, 16, 10).mean(axis=(1, 3)).ravel())
                lap = (4 * gray[1:-1, 1:-1] - gray[:-2, 1:-1] - gray[2:, 1:-1]
                       - gray[1:-1, :-2] - gray[1:-1, 2:])
                values['sharp'].append(float(np.mean(lap ** 2)))
                values['contrast'].append(float(gray.std()))
                values['delta'].append(float(np.abs(rgb - previous).mean()) if previous is not None else 0.)
                previous = rgb
            if proc.wait() != 0:
                err.seek(0)
                raise ValueError(err.read().decode(errors='replace'))
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    if len(values['x']) != len(pts):
        raise ValueError('Decoded frame count differs from timestamp count')
    data = {key: np.asarray(value, dtype=np.float32) for key, value in values.items()}
    data['pts'] = pts
    data['ts'] = pts - pts[0]
    d = data['delta']
    stability = 1 / (1 + 8 * np.maximum(d, np.r_[d[1:], d[-1]]))
    data['quality'] = np.sqrt(data['sharp']) * stability * np.clip(data['contrast'] / .06, 0, 1)
    return probe, data


def distance(data, ids, anchor):
    spatial = np.abs(data['x'][ids] - data['x'][anchor]).reshape(-1, 16, 16, 3)
    global_diff = spatial.mean(axis=(1, 2, 3))
    local = spatial.reshape(-1, 4, 4, 4, 4, 3).mean(axis=(2, 4, 5)).max(axis=(1, 2))
    color = np.abs(data['h'][ids] - data['h'][anchor]).sum(axis=1) / 6
    structure = np.abs(data['z'][ids] - data['z'][anchor]).mean(axis=1)
    return np.maximum(np.maximum(global_diff, .5 * local) + .2 * color, .35 * structure)


def boundaries(data):
    d, x, z, ts = (data[key] for key in ('delta', 'x', 'z', 'ts'))
    hd = np.r_[0, np.abs(np.diff(data['h'], axis=0)).sum(axis=1) / 6]
    zd = np.r_[0, np.abs(np.diff(z, axis=0)).mean(axis=1)]
    jumps = d + .4 * hd + .3 * zd
    candidates = []
    for i in range(1, len(d)):
        local = d[max(0, i-12):i+13]
        median = np.median(local)
        threshold = max(.08, median + 6 * np.median(np.abs(local - median)))
        if ((d[i] > threshold and hd[i] > .16) or
                (d[i] > .22 and hd[i] > .12) or (hd[i] > .30 and d[i] > .08)):
            candidates.append(i)
    flashes = {j for i in candidates if i + 1 in candidates and i + 1 < len(d)
               and np.abs(x[i-1] - x[i+1]).mean() < .035 for j in (i, i+1)}
    cuts = []
    for i in candidates:
        if i in flashes:
            continue
        if not cuts or ts[i] - ts[cuts[-1]] >= .12:
            cuts.append(i)
        elif d[i] + hd[i] > d[cuts[-1]] + hd[cuts[-1]]:
            cuts[-1] = i
    for i in range(2, len(d)-2):
        local = jumps[max(1, i-12):i+13]
        median = np.median(local)
        if (jumps[i] > max(.10, median + 5 * np.median(np.abs(local-median)))
                and zd[i] > .12 and (d[i] > .04 or hd[i] > .08)):
            cuts.append(i)
    merged = []
    for i in sorted(set(cuts)):
        if merged and i - merged[-1] <= 1:
            if jumps[i] > jumps[merged[-1]]:
                merged[-1] = i
        else:
            merged.append(i)
    return [0] + merged + [len(d)], jumps


def build_segments(data):
    bounds, jumps = boundaries(data)
    quality, contrast = data['quality'], data['contrast']
    segments = []
    for lo, hi in zip(bounds, bounds[1:]):
        candidates = set()
        residual = []
        stack = [(lo, hi, 0)]
        while stack:
            a, b, depth = stack.pop()
            q = quality[a:b].copy()
            if b-a > 4:
                q[[0, -1]] *= .75
            rep = a + int(np.argmax(q))
            dist = distance(data, np.arange(a, b), rep)
            novelty = (dist > .16) & (contrast[a:b] > .022)
            runs = []
            start = None
            for k, value in enumerate(np.r_[novelty, False]):
                if value and start is None:
                    start = k
                if not value and start is not None:
                    if k-start >= 3:
                        runs.append((a+start, a+k, float(dist[start:k].max())))
                    start = None
            split = None
            if runs and b-a >= 6 and depth < 30:
                left, right, _ = max(runs, key=lambda r: r[2])
                target = left if left > rep else right
                options = range(max(a+2, target-2), min(b-2, target+2)+1)
                split = max(options, key=lambda k: jumps[k], default=None)
            if split is not None:
                stack.extend([(split, b, depth+1), (a, split, depth+1)])
            else:
                candidates.add(rep)
                if runs:
                    residual.append({'start_frame': a, 'end_frame': b, 'difference': float(dist.max())})
        late = lo + int((hi-lo)*.65)
        candidates.add(late + int(np.argmax(quality[late:hi])))
        # Keep one candidate even for a flat transition, and preserve dark content.
        kept = []
        for i in sorted(candidates, key=lambda i: quality[i], reverse=True):
            if not any(abs(data['ts'][i]-data['ts'][j]) < 2 and
                       distance(data, [i], j)[0] < .012 for j in kept):
                kept.append(i)
        rep = max(kept, key=lambda i: quality[i])
        segments.append({'id': len(segments), 'start_frame': lo, 'end_frame_exclusive': hi,
                         'representative': rep, 'candidate_indices': sorted(kept),
                         'uncovered_persistent_runs': residual})
    return segments


def segment_anchors(segment, delivered):
    if 'start_frame' in segment:
        return sorted(i for i in delivered
                      if segment['start_frame'] <= i < segment['end_frame_exclusive'])
    return [i for i in segment['candidate_indices'] if i in delivered]


def supplemental(data, segments, delivered, count, threshold):
    seen = set(delivered)
    chosen = []
    for _ in range(count):
        options = []
        for segment in segments:
            ids = [i for i in segment['candidate_indices'] if i not in seen]
            anchors = segment_anchors(segment, seen)
            if not ids:
                continue
            if not anchors:
                i = max(ids, key=lambda i: data['quality'][i])
                options.append((float('inf'), i, segment['id']))
            else:
                residual = np.min([distance(data, ids, j) for j in anchors], axis=0)
                k = int(np.argmax(residual))
                options.append((float(residual[k]), ids[k], segment['id']))
        if not options:
            break
        score, i, segment = max(options)
        if score < threshold:
            break
        chosen.append({'frame_index': i, 'segment': segment,
                       'residual_difference': score if np.isfinite(score) else None,
                       'reason': 'unrepresented_segment' if not np.isfinite(score) else 'unseen_visual_change'})
        seen.add(i)
    return chosen


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def export_frames(source, session, indices, data, folder):
    indices = sorted(set(int(i) for i in indices))
    if not indices:
        return []
    dest = session / folder
    dest.mkdir()
    # A filter file avoids command-length limits with many selected frames.
    script = dest / 'selection.ffmpeg'
    script.write_text("select='" + '+'.join(f'eq(n,{i})' for i in indices) + "'")
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(source), '-map', '0:v:0',
                    '-filter_script:v', str(script), '-fps_mode', 'vfr', '-q:v', '2',
                    str(dest/'%04d.jpg')], check=True)
    files = sorted(dest.glob('*.jpg'))
    if len(files) != len(indices):
        raise ValueError('Export count differs from selected frames')
    return [{'frame_index': i, 'seconds': float(data['ts'][i]), 'source_pts': float(data['pts'][i]),
             'path': str(f.resolve())} for i, f in zip(indices, files)]


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def prepare(args):
    start = time.perf_counter()
    source = Path(args.video).resolve(strict=True)
    session = Path(args.out).resolve() if args.out else Path(tempfile.mkdtemp(prefix='video-analysis-'))
    if args.out:
        session.mkdir(parents=True, exist_ok=False)
    probe, data = read_features(source)
    segments = build_segments(data)
    all_reps = [s['representative'] for s in segments]
    positions = np.unique(np.rint(np.linspace(0, len(all_reps)-1, min(args.max_initial, len(all_reps)))).astype(int))
    reps = [all_reps[i] for i in positions]
    np.savez_compressed(session/'features.npz', **data)
    frames = export_frames(source, session, reps, data, 'initial')
    state = {'version': VERSION, 'source': str(source), 'source_sha256': digest(source),
             'segments': segments, 'initial_indices': reps, 'requests': [], 'extra_budget': args.extra_budget}
    save(session/'state.json', state)
    public_segments = []
    for s in segments:
        a, b = s['start_frame'], s['end_frame_exclusive']
        public_segments.append({'id': s['id'], 'start_seconds': float(data['ts'][a]),
                                'last_frame_seconds': float(data['ts'][b-1]),
                                'initial_frame_index': s['representative'] if s['representative'] in reps else None,
                                'remaining_candidates': len(s['candidate_indices'])-(s['representative'] in reps),
                                'persistent_residual': bool(s['uncovered_persistent_runs'])})
    result = {'session': str(session), 'source': str(source), 'decoded_frames': len(data['ts']),
              'candidate_frames': sum(len(s['candidate_indices']) for s in segments),
              'segments': public_segments, 'frames': frames, 'extra_budget': args.extra_budget,
              'initial_cap_omitted_segments': len(all_reps)-len(reps),
              'elapsed_seconds': time.perf_counter()-start,
              'note': 'Images delivered, not yet visually reviewed. No OCR or semantic quality judgment.'}
    save(session/'initial.json', result)
    return result


def request(args):
    session = Path(args.session).resolve(strict=True)
    with (session/'requests.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads((session/'state.json').read_text())
        source = Path(state['source'])
        if digest(source) != state['source_sha256']:
            raise ValueError('Source changed; prepare a new session')
        with np.load(session/'features.npz') as cache:
            data = {k: cache[k] for k in cache.files}
        previous = {f['frame_index'] for r in state['requests'] for f in r['frames']}
        delivered = set(state['initial_indices']) | previous
        budget = state['extra_budget'] - sum(len(r['frames']) for r in state['requests'])
        count = min(args.count, budget)
        if count <= 0:
            raise ValueError('Additional image budget exhausted')
        info = {}
        if args.command == 'supplement':
            chosen = supplemental(data, state['segments'], delivered, count, args.threshold)
            ids = [r['frame_index'] for r in chosen]
            info['selection'] = chosen
        elif args.command == 'request':
            segment = next((s for s in state['segments'] if s['id'] == args.segment), None)
            if segment is None:
                raise ValueError('Unknown numeric segment')
            ids = []
            available = [i for i in segment['candidate_indices'] if i not in delivered]
            for k in range(min(count, len(available))):
                if args.mode == 'late' and k == 0:
                    i = max(available)
                else:
                    anchors = segment_anchors(segment, delivered | set(ids))
                    i = (available[int(np.argmax(np.min([distance(data, available, j) for j in anchors], axis=0)))]
                         if anchors else max(available, key=lambda j: data['quality'][j]))
                ids.append(i)
                available.remove(i)
            info.update(segment=args.segment, mode=args.mode)
        else:
            if not np.isfinite([args.start, args.end]).all() or args.start < 0 or args.end < args.start:
                raise ValueError('Require 0 <= start <= end')
            available = np.where((data['ts'] >= args.start) & (data['ts'] <= args.end))[0]
            # Sequences may intentionally repeat earlier images to show local context.
            positions = np.unique(np.rint(np.linspace(0, len(available)-1, min(count, len(available)))).astype(int)) if len(available) else []
            ids = [int(available[k]) for k in positions]
            info.update(start=args.start, end=args.end, source_frames_in_range=len(available),
                        all_source_frames_included=len(ids) == len(available))
        folder = tempfile.mkdtemp(prefix='extra-', dir=session)
        Path(folder).rmdir()
        frames = export_frames(source, session, ids, data, Path(folder).name)
        record = {'kind': args.command, 'reason': args.reason, **info, 'frames': frames}
        state['requests'].append(record)
        save(session/'state.json', state)
        return {'session': str(session), **record, 'images_remaining': budget-len(frames),
                'note': 'Inspect returned images before making visual claims.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('video')
    prep.add_argument('--out', help='New persistent directory; default is a temporary session')
    prep.add_argument('--max-initial', type=int, default=32)
    prep.add_argument('--extra-budget', type=int, default=12)
    for name in ('request', 'supplement', 'sequence'):
        cmd = sub.add_parser(name)
        cmd.add_argument('session')
        cmd.add_argument('--count', type=int, default=4 if name == 'supplement' else 3 if name == 'request' else 12)
        cmd.add_argument('--reason', required=True)
        if name == 'request':
            cmd.add_argument('--segment', type=int, required=True)
            cmd.add_argument('--mode', choices=['novelty', 'late'], default='novelty')
        elif name == 'supplement':
            cmd.add_argument('--threshold', type=float, default=.08)
        else:
            cmd.add_argument('--start', type=float, required=True)
            cmd.add_argument('--end', type=float, required=True)
    args = parser.parse_args()
    if args.command == 'prepare' and (args.max_initial < 1 or args.extra_budget < 0):
        parser.error('Positive initial count and non-negative additional budget required')
    if args.command != 'prepare' and args.count < 1:
        parser.error('Positive count required')
    if args.command == 'supplement' and (not np.isfinite(args.threshold) or args.threshold < 0):
        parser.error('Finite non-negative threshold required')
    try:
        result = prepare(args) if args.command == 'prepare' else request(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
