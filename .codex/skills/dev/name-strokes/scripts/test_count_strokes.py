import csv
import json
from pathlib import Path
import subprocess
import sys
import os
import tempfile
import unittest
from unittest.mock import patch
from count_strokes import Engine, ROOT, resolve_data_path
from audit_corpus import audit


class StrokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.fixture = Path(cls.tmp.name).resolve()/'synthetic_corpus.json'
        cls.synthetic = {'source_kind': 'synthetic_test_fixture', 'results': [
            {'target_strokes':n, 'input':'一'*n, 'result':{
                'result_num':n, 'result_mark':'○',
                'result_content':f'SYNTHETIC PRIMARY {n}\n',
                'result_follow':f'SYNTHETIC FOLLOW {n}\n'}} for n in (1,8,120)]}
        cls.fixture.write_text(json.dumps(cls.synthetic),encoding='utf-8')
        cls.engine = Engine(data_path=cls.fixture)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_browser_success_regressions(self):
        # URL parsing quirks are intentionally repaired by the practical calculator.
        with (ROOT/'references/社名占い_実測.csv').open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                if r['表示総画数'] and int(r['試験ID']) not in {69,71,73}:
                    with self.subTest(id=r['試験ID'], name=r['入力']):
                        self.assertEqual(self.engine.count(r['入力'],profile='site-inspired')['total'], int(r['表示総画数']))

    def test_canonical_and_width_voicing(self):
        for s in ['が', 'か\u3099', 'か゛']:
            self.assertEqual(self.engine.count(s)['total'], 5)
        for s in ['ガ', 'カ\u3099', 'ｶﾞ']:
            self.assertEqual(self.engine.count(s)['total'], 4)
        for s in ['ぱ', 'は\u309a', 'ﾊﾟ']:
            self.assertEqual(self.engine.count(s)['total'], 4 if s!='ﾊﾟ' else 3)
        self.assertEqual(self.engine.count('Ａａ０')['total'], 6)

    def test_old_forms_remain_distinct(self):
        self.assertEqual(self.engine.count('国')['total'], 8)
        self.assertEqual(self.engine.count('國')['total'], 11)
        self.assertEqual(self.engine.count('高')['total'], 10)
        self.assertEqual(self.engine.count('髙')['total'], 11)

    def test_supplementary_han_has_public_provenance(self):
        r = self.engine.count('一𠮷一',han_fallback='unihan')
        self.assertEqual(r['total'], 8)
        self.assertIn(r['breakdown'][1]['basis'], ['public_data','japanese_data'])
        self.assertEqual(r['fortune']['status'], 'conditional_reference')

    def test_ivs_is_visible_extension(self):
        r = self.engine.count('高\U000e0100')
        self.assertEqual(r['total'], 10)
        self.assertTrue(r['normalization_events'])
        self.assertTrue(r['has_estimates_or_extensions'])

    def test_url_symbols_are_counted_literally(self):
        self.assertEqual(self.engine.count('一+一')['total'], 4)
        self.assertEqual(self.engine.count('一#一')['total'], 6)
        self.assertEqual(self.engine.count('一&一&一')['total'], 7)
        self.assertEqual(self.engine.count('一－一')['total'], 3)
        self.assertEqual(self.engine.count('一＋一')['total'], 4)
        self.assertEqual(self.engine.count('一#一',symbols='ignore')['total'], 2)

    def test_unknown_is_not_zero_and_does_not_choose_fortune(self):
        r = self.engine.count('一🧪一')
        self.assertIsNone(r['total'])
        self.assertEqual(r['known_subtotal'], 2)
        self.assertFalse(r['complete'])
        self.assertEqual(r['fortune']['status'], 'unknown_total')
        self.assertEqual(r['breakdown'][1]['basis'], 'unknown')

    def test_explicit_override_is_labelled(self):
        r = self.engine.count('一🧪一', overrides={'🧪': 5})
        self.assertEqual(r['total'], 7)
        self.assertEqual(r['breakdown'][1]['basis'], 'user_override')

    def test_corporate_default_and_option(self):
        self.assertEqual(self.engine.count('株式会社一')['total'], 30)
        self.assertEqual(self.engine.count('一株式会社')['total'], 30)
        self.assertEqual(self.engine.count('株式会社一',strip_corporate=True)['total'], 1)
        r = self.engine.count('株式会社株',strip_corporate=True)
        self.assertEqual(r['total'], 10)
        self.assertEqual([x['source_start'] for x in r['breakdown'] if x['strokes']], [4])
        self.assertEqual(self.engine.count('  株式会社 一 合同会社 ',strip_corporate=True)['total'], 1)

    def test_japanese_data_has_priority_and_site_is_separate(self):
        r = self.engine.count('は')
        self.assertEqual(r['total'],3)
        self.assertEqual(r['breakdown'][0]['basis'],'japanese_data')
        self.assertEqual(r['breakdown'][0]['site_reference']['strokes'],4)
        self.assertTrue(r['breakdown'][0]['differs_from_site_observation'])
        self.assertEqual(self.engine.count('は',profile='site-inspired')['total'],4)
        self.assertEqual(self.engine.count('有限会社一')['total'],29)

    def test_unihan_is_opt_in(self):
        char = next(c for c in self.engine.unihan['counts']
                    if c not in self.engine.kanjivg['counts'] and c not in self.engine.rules['characters'])
        self.assertIsNone(self.engine.count(char)['total'])
        r = self.engine.count(char,han_fallback='unihan')
        self.assertIsInstance(r['total'],int)
        self.assertEqual(r['breakdown'][0]['basis'],'public_data')

    def test_120_boundary_never_wraps(self):
        a = self.engine.count('一'*120)
        b = self.engine.count('一'*121)
        self.assertEqual(a['fortune']['result_num'], 120)
        self.assertEqual(b['total'], 121)
        self.assertEqual(b['fortune']['status'], 'out_of_range')
        self.assertNotIn('result_content', b['fortune'])
        self.assertEqual(self.engine.count(' ')['fortune']['status'], 'out_of_range')

    def test_synthetic_fortune_is_unmodified(self):
        for entry in self.synthetic['results']:
            with self.subTest(n=entry['target_strokes']):
                r = self.engine.count(entry['input'])['fortune']
                self.assertEqual(r['result_num'],entry['target_strokes'])
                self.assertEqual(r['result_content'],entry['result']['result_content'])
                self.assertEqual(r['result_follow'],entry['result']['result_follow'])
        self.assertEqual(self.engine.count('一'*75)['fortune']['status'], 'result_not_available')

    def test_accents_are_explicit_normalization(self):
        a, b = self.engine.count('é'), self.engine.count('e\u0301')
        self.assertEqual(a['total'], b['total'])
        self.assertEqual(a['normalized_input'],'e')
        self.assertTrue(a['normalization_events'])

    def test_missing_corpus_audit(self):
        r = audit(data_path=Path(self.tmp.name)/'not-installed.json')
        self.assertFalse(r['ok'])
        self.assertEqual(r['status'],'data_not_configured')

    def test_counting_without_private_data(self):
        engine = Engine(data_path=Path(self.tmp.name)/'not-installed.json')
        r = engine.count('Spool')
        self.assertEqual(r['total'],6)
        self.assertEqual(r['fortune']['status'],'data_not_configured')
        self.assertNotIn('result_content',r['fortune'])

    def test_bad_private_data_preserves_counting(self):
        p = Path(self.tmp.name)/'broken.json'
        p.write_text('{"unexpected":[]}',encoding='utf-8')
        r = Engine(data_path=p).count('一')
        self.assertEqual(r['total'],1)
        self.assertEqual(r['fortune']['status'],'data_error')

    def test_data_path_priority(self):
        with patch.dict(os.environ,{'NAME_STROKES_DATA':'','XDG_DATA_HOME':self.tmp.name}):
            self.assertEqual(resolve_data_path(),Path(self.tmp.name).resolve()/'name-strokes/shamei_uranai_1-120.json')
        with patch.dict(os.environ,{'NAME_STROKES_DATA':str(self.fixture)}):
            self.assertEqual(resolve_data_path(),self.fixture)
            self.assertEqual(resolve_data_path(Path(self.tmp.name)/'explicit.json'),Path(self.tmp.name).resolve()/'explicit.json')

    def test_cli_batch_unknown_strict(self):
        p = subprocess.run([sys.executable,str(ROOT/'scripts/count_strokes.py'),'一','一🧪一','--json','--strict','--data',str(self.fixture)],capture_output=True,text=True)
        self.assertEqual(p.returncode,2)
        out=json.loads(p.stdout)
        self.assertEqual(out[0]['total'],1)
        self.assertIsNone(out[1]['total'])

    def test_cli_public_environment_without_data(self):
        env = os.environ.copy()
        env['XDG_DATA_HOME'] = str(Path(self.tmp.name)/'isolated-data')
        env.pop('NAME_STROKES_DATA',None)
        p = subprocess.run([sys.executable,str(ROOT/'scripts/count_strokes.py'),'ガント','--json'],capture_output=True,text=True,env=env)
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout)[0]
        self.assertEqual(result['total'],8)
        self.assertEqual(result['fortune']['status'],'data_not_configured')

    def test_cli_rejects_invalid_override(self):
        p = subprocess.run([sys.executable,str(ROOT/'scripts/count_strokes.py'),'一','--override','一=-1'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2)


if __name__ == '__main__':
    unittest.main()
