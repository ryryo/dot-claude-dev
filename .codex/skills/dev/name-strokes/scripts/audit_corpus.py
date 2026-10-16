#!/usr/bin/env python3
"""Validate the user-supplied corpus without changing it or contacting the website."""
from collections import Counter
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
from count_strokes import CORPUS_SHA256, Engine, ROOT, resolve_data_path


def fnv1a32(s):
    value = 2166136261
    # Match JavaScript charCodeAt (UTF-16 code units), including non-BMP characters.
    raw = s.encode('utf-16-le')
    for i in range(0, len(raw), 2):
        value = ((value ^ int.from_bytes(raw[i:i+2], 'little')) * 16777619) & 0xffffffff
    return format(value, 'x')


def audit(root=ROOT, data_path=None):
    root = Path(root)
    path = resolve_data_path(data_path)
    if not path.exists():
        return {'ok': False, 'status': 'data_not_configured', 'data_path': str(path),
                'reason': '鑑定データ未設定。計数はデータなしで利用できます。'}
    raw = path.read_bytes()
    duplicate_json_keys = []
    def pairs(items):
        d = {}
        for key, value in items:
            if key in d:
                duplicate_json_keys.append(key)
            d[key] = value
        return d
    document = json.loads(raw, object_pairs_hook=pairs)
    entries = document['results']
    counts = Counter(e['target_strokes'] for e in entries)
    engine = Engine(root, data_path=path)
    mismatch = [e['target_strokes'] for e in entries
                if e['target_strokes'] != e['result']['result_num']
                or not e['stroke_count_matches'] or e['http_status'] != 200]
    input_mismatch = [e['target_strokes'] for e in entries
                      if engine.count(e['input'], fortune=False)['total'] != e['target_strokes']]
    templates = {re.sub('[0-9０-９]+', '#', e['result']['result_content']) for e in entries}
    by_number = {e['target_strokes']: e for e in entries}
    compared, content_mismatch, rating_mismatch = set(), [], []
    with (root/'references/社名占い_実測.csv').open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            if not row['表示総画数'] or not row['本文指紋FNV1a32']:
                continue
            n = int(row['表示総画数'])
            result = by_number[n]['result']
            rendered_text = (result['result_content']+result['result_follow']).replace('\r', '').replace('\n', '')
            if fnv1a32(rendered_text) != row['本文指紋FNV1a32']:
                content_mismatch.append(int(row['試験ID']))
            mark_stars = {'×': '0', '△': '1', '○': '2', '◎': '3'}
            if mark_stars.get(result['result_mark']) != row['星数_画像ファイル名より']:
                rating_mismatch.append(int(row['試験ID']))
            compared.add(n)
    report = {'source': 'user_provided_original', 'bytes': len(raw),
              'data_path': str(path),
              'sha256': hashlib.sha256(raw).hexdigest(), 'expected_sha256': CORPUS_SHA256,
              'entry_count': len(entries), 'missing': sorted(set(range(1,121))-set(counts)),
              'duplicate_strokes': [k for k,v in counts.items() if v>1],
              'duplicate_json_keys': duplicate_json_keys, 'result_mismatch': mismatch,
              'fixture_count_mismatch': input_mismatch,
              'empty_primary_text': [e['target_strokes'] for e in entries if not e['result']['result_content']],
              'empty_follow_count': sum(not e['result']['result_follow'] for e in entries),
              'empty_follow_only_good_marks': all(bool(e['result']['result_follow']) == (e['result']['result_mark'] in {'△','×'}) for e in entries),
              'mark_counts': dict(Counter(e['result']['result_mark'] for e in entries)),
              'digit_normalized_primary_template_count': len(templates),
              'browser_observed_totals_compared': len(compared),
              'browser_content_fingerprint_mismatch_ids': sorted(set(content_mismatch)),
              'browser_rating_mismatch_ids': sorted(set(rating_mismatch)),
              'text_modified': False, 'website_refetched': False}
    report['ok'] = (report['sha256']==CORPUS_SHA256 and len(entries)==120
                    and not any([report['missing'], report['duplicate_strokes'], duplicate_json_keys,
                                 mismatch, input_mismatch, report['empty_primary_text'],
                                 content_mismatch, rating_mismatch]))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', metavar='FILE', help='ローカル鑑定JSONを明示指定')
    args = parser.parse_args()
    result = audit(data_path=args.data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
