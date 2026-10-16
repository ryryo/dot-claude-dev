#!/usr/bin/env python3
"""Extract stroke properties from an explicitly supplied Unicode 17 archive. No network."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(archive, output):
    counts, alternate, japanese = {}, {}, {}
    with zipfile.ZipFile(archive) as z:
        for filename in z.namelist():
            for line in z.read(filename).decode('utf-8').splitlines():
                if not line or line.startswith('#'):
                    continue
                cp, field, value = line.split('\t', 2)
                char = chr(int(cp[2:], 16))
                if field == 'kTotalStrokes':
                    counts[char] = int(value)
                elif field == 'kAlternateTotalStrokes' and value != '-':
                    entries = [part.split(':') for part in value.split()]
                    alternate[char] = sorted({int(n) for n, _ in entries})
                    for n, regions in entries:
                        if 'J' in regions:
                            japanese[char] = int(n)
    if len(counts) < 90000:
        raise ValueError('Unexpectedly small Unihan archive')
    data = {'unicode_version': '17.0.0', 'license': 'Unicode-3.0',
            'archive_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
            'source_url': 'https://www.unicode.org/Public/17.0.0/ucd/Unihan.zip',
            'counts': counts, 'japanese_overrides': japanese, 'alternate_counts': alternate}
    Path(output).write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    print(json.dumps({'characters': len(counts), 'japanese_overrides': len(japanese),
                      'archive_sha256': data['archive_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.archive, args.output)
