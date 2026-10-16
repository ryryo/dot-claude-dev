#!/usr/bin/env python3
"""Extract base-character SVG stroke counts from a pinned KanjiVG archive (offline)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


def build(archive, source_metadata, output, license_output):
    meta = json.loads(Path(source_metadata).read_text(encoding='utf-8'))
    digest = hashlib.sha256(Path(archive).read_bytes()).hexdigest()
    if digest != meta['archive_sha256']:
        raise ValueError('KanjiVG archive digest mismatch')
    counts = {}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            match = re.search(r'/kanji/([0-9a-f]{5})\.svg$', name)
            if match:
                root = ET.fromstring(z.read(name))
                paths = root.findall('.//{http://www.w3.org/2000/svg}path')
                n = sum(bool(re.search(r'-s\d+$', p.attrib.get('id',''))) for p in paths)
                if n:
                    counts[chr(int(match[1],16))] = n
        copying = next(n for n in z.namelist() if n.endswith('/COPYING'))
        Path(license_output).write_bytes(z.read(copying))
    if len(counts) < 6000:
        raise ValueError('Unexpectedly small KanjiVG base-character data')
    data = {**meta, 'source_project':'KanjiVG',
            'copyright':'Ulrich Apel and contributors',
            'transformation':'Count paths with stroke IDs in base Unicode SVG filenames; variant-suffixed files excluded.',
            'counts':counts}
    Path(output).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'characters':len(counts),'commit':meta['commit'],
                      'sample':{c:counts.get(c) for c in '有限はぱ高髙国國'}},ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ['archive','source_metadata','output','license_output']:
        p.add_argument(arg,type=Path)
    a = p.parse_args()
    build(a.archive,a.source_metadata,a.output,a.license_output)
