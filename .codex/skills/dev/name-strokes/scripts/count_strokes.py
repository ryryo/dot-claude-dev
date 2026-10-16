#!/usr/bin/env python3
"""Offline, evidence-labelled stroke estimates for Japanese business/service names."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import unicodedata as ud

ROOT = Path(__file__).resolve().parents[1]
CORPUS_SHA256 = '6b004c1e0c96d55563ff62a4923551fd95fd1b3ea905ce384fa783ed776c8ed9'
MARK_STARS = {'×': 0, '△': 1, '○': 2, '◎': 3}
CORPORATE = ('株式会社', '有限会社', '合同会社', '合資会社', '合名会社')


def resolve_data_path(explicit=None):
    """Private user data lives outside the repository; never auto-load bundled assets."""
    value = explicit or os.environ.get('NAME_STROKES_DATA')
    if value:
        return Path(value).expanduser().resolve()
    base = Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')
    return (base/'name-strokes/shamei_uranai_1-120.json').expanduser().resolve()

# Explicit handwriting conventions, not individually observed website values.
# A/a and the total of each alphabet are observed; other assignments are not unique.
UPPER = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                 [3,3,1,2,4,3,2,3,1,1,3,2,4,3,1,2,2,3,1,2,1,2,4,2,2,2]))
LOWER = dict(zip('abcdefghijklmnopqrstuvwxyz',
                 [2,2,1,2,2,2,2,2,2,2,3,1,3,2,1,2,2,2,1,2,2,2,4,2,3,3]))
HIRA = dict(zip('あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわゐゑをん',
                [3,2,2,2,3,3,4,1,3,2,3,1,2,3,1,4,2,1,1,2,4,3,2,2,1,4,1,4,1,5,3,2,3,2,3,3,2,2,2,2,1,2,1,2,3,5,3,1]))
KATA = dict(zip('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヰヱヲン',
                [2,2,3,3,3,2,3,2,3,2,3,3,2,2,2,3,3,3,3,2,2,2,2,4,1,2,2,1,2,4,2,3,2,2,3,2,2,3,2,2,2,1,3,2,4,3,3,2]))
SMALL = dict(zip('ぁぃぅぇぉっゃゅょゎゕゖァィゥェォッャュョヮヵヶ',
                 'あいうえおつやゆよわかけアイウエオツヤユヨワカケ'))
SYMBOLS = {'+':2, '#':4, '_':1, '@':2, '%':4, '(':1, ')':1,
           '[':1, ']':1, '{':1, '}':1, '/':1, '\\':1, ':':2, ';':2,
           '!':2, '?':2, '*':3, '=':2, '$':3, '€':3, '£':3,
           ',':1, '、':1, '。':1, '「':1, '」':1, '『':2, '』':2,
           '〈':1, '〉':1, '《':2, '》':2, '゛':2, '゜':1}
DASHES = set('‐‑‒–—―−')


def codepoints(s):
    return ['U+%04X' % ord(c) for c in s]


def is_han(c):
    n = ord(c)
    return (0x3400 <= n <= 0x9fff or 0xf900 <= n <= 0xfaff
            or 0x20000 <= n <= 0x323ff)


def is_selector(c):
    return 0xfe00 <= ord(c) <= 0xfe0f or 0xe0100 <= ord(c) <= 0xe01ef


def kana(c):
    return 0x3040 <= ord(c) <= 0x30ff or 0xff66 <= ord(c) <= 0xff9d


def normalize_units(text):
    """Keep a reversible source span; protect CJK compatibility ideographs from NFKC."""
    groups = []
    for i, c in enumerate(text):
        attach = bool(groups) and (ud.combining(c) or is_selector(c)
                 or (c in '\u309b\u309c\uff9e\uff9f' and kana(groups[-1][1][0])))
        if attach:
            groups[-1][1] += c
        else:
            groups.append([i, c])
    units, events = [], []
    for pos, raw in groups:
        notes = []
        value = ''.join(c for c in raw if not is_selector(c))
        if value != raw:
            notes.append('異体字セレクタを除き基底字で補完（字体固有の画数は未確認）')
        if value and kana(value[0]):
            value = value.replace('\u309b', '\u3099').replace('\u309c', '\u309a')
        if value and is_han(value[0]):
            # NFC also folds some compatibility ideographs; preserve the base explicitly.
            value = value[0] + ud.normalize('NFC', value[1:])
        else:
            value = ud.normalize('NFKC', value)
        value = ''.join('-' if c in DASHES else c for c in value)
        # Accent folding is an explicit practical extension, never a website observation.
        folded = ud.normalize('NFD', value)
        if folded and folded[0].isascii() and folded[0].isalpha() and any(ud.combining(c) for c in folded):
            value = ''.join(c for c in folded if not ud.combining(c))
            notes.append('Latinアクセントを基底英字へ補完')
        if value != raw:
            events.append({'source_start': pos, 'original': raw, 'normalized': value,
                           'reason': notes or ['NFKC/NFC・幅・濁点・ダッシュ表記の統一']})
        for c in value:
            units.append({'character': c, 'input_fragment': raw, 'source_start': pos,
                          'source_codepoints': codepoints(raw), 'normalization_notes': notes})
        if not value:
            units.append({'character': '', 'input_fragment': raw, 'source_start': pos,
                          'source_codepoints': codepoints(raw), 'normalization_notes': notes})
    return units, events


class Engine:
    def __init__(self, root=ROOT, data_path=None):
        self.root = Path(root)
        self.rules = json.loads((self.root/'assets/observed_strokes.json').read_text(encoding='utf-8'))
        self.kanjivg = json.loads((self.root/'assets/kanjivg_strokes.json').read_text(encoding='utf-8'))
        self.unihan = json.loads((self.root/'assets/unihan_strokes.json').read_text(encoding='utf-8'))
        self.data_path = resolve_data_path(data_path)
        self.fortunes, self.corpus_sha256, self.data_error = {}, None, None
        self.corpus_source = 'local_user_data'
        if self.data_path.exists():
            try:
                raw = self.data_path.read_bytes()
                self.corpus_sha256 = hashlib.sha256(raw).hexdigest()
                document = json.loads(raw)
                entries = document['results']
                keys = [e['target_strokes'] for e in entries]
                if not keys or len(set(keys)) != len(keys) or any(type(n) is not int or not 1 <= n <= 120 for n in keys):
                    raise ValueError('鑑定番号が重複または範囲外です')
                for e in entries:
                    r = e['result']
                    if r['result_num'] != e['target_strokes'] or not isinstance(r['result_content'], str) or not r['result_content'] or r['result_mark'] not in MARK_STARS or not isinstance(r.get('result_follow', ''), str):
                        raise ValueError('鑑定画数・本文・印が不正です')
                self.fortunes = {e['target_strokes']: e for e in entries}
                self.corpus_source = document.get('source_kind', 'local_user_data')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.data_error = str(exc)

    def lookup(self, c, symbols='count', overrides=None, profile='japanese', han_fallback='none'):
        if overrides and c in overrides:
            return overrides[c], 'user_override', 'CLI --override', 'ユーザー指定。サイト実測値ではない', []
        if not c or c.isspace():
            return 0, 'policy', 'whitespace-policy', '空白・空の正規化結果は0画として扱う', []
        if symbols == 'ignore' and ud.category(c)[0] in 'PS':
            return 0, 'policy', '--symbols ignore', '明示オプションにより記号を除外', []
        japanese_value = self.kanjivg['counts'].get(c) if is_han(c) or kana(c) else None
        if profile == 'japanese' and japanese_value is not None:
            return japanese_value, 'japanese_data', 'KanjiVG:'+self.kanjivg['commit'][:12], '日本語の筆順SVGの筆画数。サイト計数値とは区別', []
        if c in self.rules['characters']:
            rule = self.rules['characters'][c]
            if profile == 'japanese' and (is_han(c) or kana(c)):
                return rule['strokes'], 'observed_site_fallback', rule['source'], '日本語データ未収録。サイト実測値を参考採用し、日本語筆画の確定値とはしない', []
            return rule['strokes'], rule['basis'], rule['source'], rule.get('note', ''), []
        if japanese_value is not None:
            return japanese_value, 'japanese_data', 'KanjiVG:'+self.kanjivg['commit'][:12], '日本語の筆順SVGの筆画数。サイト計数値は未確認', []
        if han_fallback == 'unihan' and c in self.unihan['counts']:
            value = self.unihan['japanese_overrides'].get(c, self.unihan['counts'][c])
            source = 'Unihan-17.0.0:kAlternateTotalStrokes:J' if c in self.unihan['japanese_overrides'] else 'Unihan-17.0.0:kTotalStrokes'
            variants = sorted({value, self.unihan['counts'][c], *self.unihan['alternate_counts'].get(c, [])})
            return value, 'public_data', source, '公開漢字データ。サイトとの一致は未検証', variants
        if c in UPPER or c in LOWER:
            return (UPPER | LOWER)[c], 'heuristic', 'latin-handwriting-v1', '手書き慣例による補完。26字総和への適合は単字値の証明ではない', []
        base = SMALL.get(c, c)
        if base in HIRA or base in KATA:
            return (HIRA | KATA)[base], 'heuristic', 'kana-handwriting-v1', 'かなの筆画慣例、小書きは通常字と同数', []
        decomposition = ud.normalize('NFD', c)
        if len(decomposition) == 2 and decomposition[1] in '\u3099\u309a':
            n, basis, source, _, alternatives = self.lookup(decomposition[0], symbols, overrides, profile, han_fallback)
            if n is not None:
                return n+(2 if decomposition[1] == '\u3099' else 1), 'heuristic', source+'+voicing', '濁点+2・半濁点+1で補完', alternatives
        if c in SYMBOLS:
            return SYMBOLS[c], 'heuristic', 'symbol-policy-v1', '明示した線・点の数による記号補完。唯一の正解やサイト実測値ではない', []
        if ud.category(c) == 'Cf':
            return 0, 'policy', 'format-character-policy', 'ゼロ幅等の書式文字を除外。原文と位置は保持', []
        if ud.category(c).startswith('P'):
            return 0, 'policy', 'other-punctuation-policy', '未定義の句読記号は区切りとして除外（警告付き）', []
        return None, 'unknown', None, '根拠のある画数なし。--override 文字=画数で明示指定できる', []

    def count(self, name, *, strip_corporate=False, symbols='count', overrides=None, fortune=True,
              profile='japanese', han_fallback='none'):
        units, events = normalize_units(name)
        normalized = ''.join(u['character'] for u in units)
        target = normalized
        if strip_corporate:
            start, stop = 0, len(normalized)
            while start < stop and normalized[start].isspace():
                start += 1
            while stop > start and normalized[stop-1].isspace():
                stop -= 1
            changed = True
            while changed:
                changed = False
                for form in CORPORATE:
                    if normalized.startswith(form, start, stop):
                        start, changed = start+len(form), True
                        while start < stop and normalized[start].isspace():
                            start += 1
                    if normalized.endswith(form, start, stop):
                        stop, changed = stop-len(form), True
                        while stop > start and normalized[stop-1].isspace():
                            stop -= 1
            target = normalized[start:stop]
            if target != normalized:
                events.append({'original': normalized, 'normalized': target,
                               'reason': ['明示オプション --strip-corporate により先頭・末尾の法人格を除外']})
        else:
            start, stop = 0, len(normalized)
        breakdown, warnings, offset = [], [], 0
        for u in units:
            c = u['character']
            excluded = strip_corporate and not start <= offset < stop
            offset += len(c)
            if excluded:
                n, basis, source, note, alts = 0, 'policy', '--strip-corporate', '法人格・端の空白を除外', []
            else:
                n, basis, source, note, alts = self.lookup(c, symbols, overrides, profile, han_fallback)
            reference = self.rules['characters'].get(c)
            breakdown.append({**u, 'codepoints': codepoints(c), 'strokes': n,
                              'basis': basis, 'source': source, 'note': note, 'alternatives': alts,
                              'site_reference': reference,
                              'differs_from_site_observation': bool(reference and not excluded and n != reference['strokes'])})
        unknown = [r for r in breakdown if r['strokes'] is None]
        subtotal = sum(r['strokes'] for r in breakdown if r['strokes'] is not None)
        total = None if unknown else subtotal
        bases = dict(Counter(r['basis'] for r in breakdown))
        estimates = bool(events or any(r['basis'] not in {'observed', 'observed_difference', 'provided_fixture'} for r in breakdown))
        if events:
            warnings.append('入力表記を正規化・補完した。original/normalizedと変換履歴を確認してください。')
        if bases.get('public_data'):
            warnings.append('明示オプションでUnihan補完を使用。日本語字体の画数とは限らず、サイト一致も未確認です。')
        if bases.get('observed_site_fallback'):
            warnings.append('日本語データ未収録の文字にサイト実測値を参考採用しています。日本語としての画数は要確認です。')
        if any(r['differs_from_site_observation'] for r in breakdown):
            warnings.append('日本語筆順データとサイト実測値が異なる文字があります。site_referenceで比較できます。')
        if bases.get('heuristic'):
            warnings.append('推定・明示補完ルールを含みます。文字別のbasis/sourceを確認してください。')
        if bases.get('policy'):
            warnings.append('空白・区切り・書式または明示オプションによる除外を含みます。')
        if unknown:
            warnings.append('未知文字: '+', '.join(repr(r['character']) for r in unknown)+'。totalは未確定、known_subtotalは既知部分のみ。')
        if any(len(r['alternatives']) > 1 for r in breakdown):
            warnings.append('地域・字体により画数候補が複数ある文字を含みます。日本向け値が公開されていれば優先しています。')
        if total == 0:
            warnings.append('計数対象が0画です。0画の原文鑑定はありません。')
        answer = {'input': name, 'normalized_input': normalized, 'calculation_input': target,
                  'normalization_events': events, 'total': total, 'known_subtotal': subtotal,
                  'complete': not unknown, 'has_estimates_or_extensions': estimates,
                  'site_full_compatibility_claimed': False, 'basis_counts': bases,
                  'trademark_status': 'not_checked',
                  'policy': {'profile': profile, 'han_fallback': han_fallback,
                             'kanjivg_commit': self.kanjivg['commit'],
                             'symbols': symbols, 'strip_corporate': strip_corporate,
                             'unicode_database_version': self.unihan['unicode_version'],
                             'python_normalization_version': ud.unidata_version},
                  'breakdown': breakdown, 'warnings': warnings}
        if fortune:
            if total is None:
                answer['fortune'] = {'status': 'unknown_total', 'reason': '未知文字が残るため鑑定番号を決めない'}
            elif not 1 <= total <= 120:
                answer['fortune'] = {'status': 'out_of_range', 'reason': '提供原文は1〜120画のみ。折り返し・循環・本文生成をしない'}
            elif self.data_error:
                answer['fortune'] = {'status': 'data_error', 'data_path': str(self.data_path),
                    'reason': 'ローカル鑑定データを読めません。計数結果は利用できます。'+self.data_error}
            elif not self.fortunes:
                answer['fortune'] = {'status': 'data_not_configured', 'data_path': str(self.data_path),
                    'reason': '鑑定データ未設定。--data FILE、NAME_STROKES_DATA、または既定のローカル保存先に利用権のあるデータを設定してください。計数はデータなしで動作します。'}
            elif total not in self.fortunes:
                answer['fortune'] = {'status': 'result_not_available', 'result_num': total,
                    'reason': 'この番号の原文はローカルデータにありません。循環・本文生成はしません。'}
            else:
                entry = self.fortunes[total]
                result = entry['result']
                answer['fortune'] = {'status': 'conditional_reference' if estimates else 'reference',
                    'source': self.corpus_source, 'source_sha256': self.corpus_sha256,
                    'data_path': str(self.data_path),
                    'result_page_url': entry.get('result_page_url'),
                    'result_num': total, 'result_mark': result['result_mark'],
                    'stars': MARK_STARS.get(result['result_mark']),
                    'result_content': result['result_content'], 'result_follow': result.get('result_follow', ''),
                    'text_status': '原文無改変・未校正',
                    'condition': 'この計数方式で得た番号の提供原文参照。入力名をサイトで鑑定済みという意味ではない'}
        return answer


def human(result, full_text=False):
    total = result['total']
    print(f"{result['input']!r}: "+(f'{total}画' if total is not None else f"総画数未確定（既知部分{result['known_subtotal']}画）"))
    print('  計数表記: '+repr(result['calculation_input']))
    for row in result['breakdown']:
        n = '?' if row['strokes'] is None else row['strokes']
        print(f"  {row['input_fragment']!r} → {row['character']!r}: {n} [{row['basis']}; {row['source']}]")
        if row['differs_from_site_observation']:
            print(f"    サイト実測値: {row['site_reference']['strokes']}画")
    for warning in result['warnings']:
        print('  注意: '+warning)
    f = result.get('fortune')
    if f and f['status'] in {'reference', 'conditional_reference'}:
        print(f"  原文参照 {f['result_num']}画: {f['result_mark']} / 星{f['stars']}（{f['text_status']}）")
        if full_text:
            print(f['result_content'])
            if f['result_follow']:
                print(f['result_follow'])
        else:
            print('  '+f['result_content'].splitlines()[0])
    elif f:
        print('  原文参照なし: '+f['reason'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='+', help='候補名。複数指定可')
    parser.add_argument('--json', action='store_true', help='配列形式のJSON。文字別根拠と原文を含む')
    parser.add_argument('--full-text', action='store_true', help='人間向け表示に鑑定原文全文を含める')
    parser.add_argument('--no-fortune', action='store_true')
    parser.add_argument('--data', metavar='FILE', help='Git管理外のローカル鑑定JSON。未指定はNAME_STROKES_DATA、次にXDG_DATA_HOME/name-strokes/（既定~/.local/share/name-strokes/）')
    parser.add_argument('--strip-corporate', action='store_true', help='先頭・末尾の日本語法人格のみ除外')
    parser.add_argument('--symbols', choices=['count', 'ignore'], default='count')
    parser.add_argument('--profile', choices=['japanese','site-inspired'], default='japanese',
                        help='既定は日本語KanjiVG優先。site-inspiredは実測値を優先（完全互換ではない）')
    parser.add_argument('--han-fallback', choices=['none','unihan'], default='none',
                        help='日本語データ未収録漢字のUnihan補完を明示的に有効化')
    parser.add_argument('--override', action='append', default=[], metavar='CHAR=COUNT')
    parser.add_argument('--strict', action='store_true', help='未知文字がある場合も全候補を出力し終了コード2')
    args = parser.parse_args(argv)
    overrides = {}
    for spec in args.override:
        try:
            char, number = spec.rsplit('=', 1)
            if len(char) != 1 or not number.isascii() or not number.isdecimal():
                raise ValueError
            overrides[char] = int(number)
        except ValueError:
            parser.error('--override はUnicode1文字=0以上の整数で指定してください')
    try:
        engine = Engine(data_path=args.data)
        results = [engine.count(name, strip_corporate=args.strip_corporate,
                    symbols=args.symbols, overrides=overrides, fortune=not args.no_fortune,
                    profile=args.profile, han_fallback=args.han_fallback) for name in args.names]
    except (ValueError, OSError, KeyError) as exc:
        print('データエラー: '+str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for i, result in enumerate(results):
            if i:
                print()
            human(result, args.full_text)
    return 2 if args.strict and any(not r['complete'] for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
