import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('pstack_setup', Path(__file__).with_name('setup.py'))
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pstack-setup-test-')
        self.base = Path(self.temp.name)
        self.source = self.base / '日本語 配布元/skills/dev/pstack-thermos'
        shutil.copytree(setup.ROOT / 'assets/agents', self.source / 'assets/agents')
        shutil.copy2(setup.ROOT / 'SKILL.md', self.source / 'SKILL.md')
        self.dest = self.base / '作業 プロジェクト/.codex'

    def tearDown(self):
        self.temp.cleanup()

    def test_check_does_not_create_files(self):
        _, rows, receipt = setup.plan(self.dest, self.source, 'check')
        self.assertFalse(self.dest.exists())
        self.assertIsNone(receipt)
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row['state'] == '未設定' for row in rows))

    def test_install_rerun_repair_and_remove_preserve_other_settings(self):
        setup.apply(self.dest, self.source, 'install')
        unrelated = self.dest / 'agents/custom.toml'
        unrelated.write_text('name = "custom"\n')
        original = (self.dest / 'agents/poteto-agent.toml').read_bytes()
        setup.apply(self.dest, self.source, 'install')
        self.assertEqual(original, (self.dest / 'agents/poteto-agent.toml').read_bytes())
        self.assertEqual((self.dest / 'skills/pstack-thermos').resolve(), self.source.resolve())
        (self.dest / 'agents/pstack-skeptic.toml').unlink()
        setup.apply(self.dest, self.source, 'install')
        self.assertTrue((self.dest / 'agents/pstack-skeptic.toml').exists())
        setup.apply(self.dest, self.source, 'uninstall')
        self.assertTrue(unrelated.exists())
        self.assertFalse((self.dest / 'skills/pstack-thermos').is_symlink())
        self.assertFalse(setup.receipt_path(self.dest).exists())

    def test_unowned_collision_stops_before_any_install(self):
        foreign = self.dest / 'agents/pstack-skeptic.toml'
        foreign.parent.mkdir(parents=True)
        foreign.write_text('利用者の設定')
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'install')
        self.assertEqual(foreign.read_text(), '利用者の設定')
        self.assertFalse((self.dest / 'skills').exists())
        self.assertFalse(setup.receipt_path(self.dest).exists())

    def test_update_only_unchanged_owned_files(self):
        setup.apply(self.dest, self.source, 'install')
        template = self.source / 'assets/agents/poteto-agent.toml'
        template.write_text(template.read_text().replace('実装・調査', '限定された実装・調査'))
        setup.apply(self.dest, self.source, 'update')
        self.assertEqual(template.read_bytes(), (self.dest / 'agents/poteto-agent.toml').read_bytes())
        edited = self.dest / 'agents/pstack-skeptic.toml'
        edited.write_text(edited.read_text() + '\n# 利用者の変更\n')
        before = setup.receipt_path(self.dest).read_bytes()
        for action in ('update', 'uninstall'):
            with self.assertRaises(ValueError):
                setup.apply(self.dest, self.source, action)
        self.assertIn('利用者の変更', edited.read_text())
        self.assertEqual(before, setup.receipt_path(self.dest).read_bytes())

    def test_refuse_destination_symlink(self):
        outside = self.base / '外部設定'
        outside.mkdir()
        self.dest.parent.mkdir(parents=True)
        self.dest.symlink_to(outside)
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'install')
        self.assertEqual(list(outside.iterdir()), [])

    def test_receipt_cannot_redirect_or_change_owner(self):
        setup.apply(self.dest, self.source, 'install')
        other = self.base / '別の配布元'
        shutil.copytree(self.source, other)
        with self.assertRaises(ValueError):
            setup.apply(self.dest, other, 'update')
        import json
        receipt = setup.receipt_path(self.dest)
        data = json.loads(receipt.read_text())
        data['entries']['../outside'] = {'kind': 'file', 'sha256': '0' * 64}
        receipt.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'uninstall')
        self.assertTrue((self.dest / 'skills/pstack-thermos').is_symlink())

    def test_io_failure_rolls_back_and_cleans_its_temporary_files(self):
        from unittest.mock import patch
        original = Path.replace
        def fail_receipt(path, target):
            if Path(target) == setup.receipt_path(self.dest):
                raise OSError('管理記録を書けない試験')
            return original(path, target)
        with patch.object(Path, 'replace', fail_receipt):
            with self.assertRaises(OSError):
                setup.apply(self.dest, self.source, 'install')
        self.assertFalse((self.dest / 'skills/pstack-thermos').is_symlink())
        self.assertFalse(list((self.dest / 'agents').glob('*.toml')))
        self.assertFalse(list(self.dest.rglob('*.tmp')))
        self.assertFalse(list(self.dest.rglob('*.pstack-tmp')))
        rows = setup.apply(self.dest, self.source, 'install')
        self.assertTrue(all(row['state'] == '配置済み' for row in rows))

    def test_existing_lock_prevents_concurrent_writes(self):
        self.dest.mkdir(parents=True)
        lock = self.dest / '.pstack-ja-setup.lock'
        lock.write_text('他の処理')
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'install')
        self.assertEqual(lock.read_text(), '他の処理')
        self.assertFalse((self.dest / 'skills').exists())

    def test_corrupt_receipt_kind_is_rejected(self):
        import json
        setup.apply(self.dest, self.source, 'install')
        receipt = setup.receipt_path(self.dest)
        data = json.loads(receipt.read_text())
        data['entries']['agents/pstack-skeptic.toml'] = {'kind': 'symlink', 'target': str(self.source)}
        receipt.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'uninstall')
        self.assertTrue((self.dest / 'agents/pstack-skeptic.toml').exists())

    def test_user_scope_uses_only_isolated_codex_home(self):
        import os, subprocess, sys, json
        home = self.base / '共通設定'
        env = dict(os.environ, CODEX_HOME=str(home))
        result = subprocess.run([sys.executable, str(setup.ROOT / 'scripts/setup.py'),
                                 'install', '--scope', 'user', '--json'],
                                env=env, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(Path(report['destination']), home)
        self.assertTrue(all(row['state'] == '配置済み' for row in report['entries']))
        self.assertEqual((home / 'skills/pstack-thermos').resolve(), setup.ROOT)
        subprocess.run([sys.executable, str(setup.ROOT / 'scripts/setup.py'),
                        'uninstall', '--scope', 'user'], env=env, capture_output=True, check=True)
        self.assertFalse((home / 'skills/pstack-thermos').is_symlink())

    def legacy_install(self):
        import json
        old_source = self.source.with_name('pstack')
        (self.dest / 'skills').mkdir(parents=True)
        (self.dest / 'agents').mkdir()
        entries = {'skills/pstack': {'kind': 'symlink', 'target': str(old_source)}}
        (self.dest / 'skills/pstack').symlink_to(old_source)
        for name in setup.AGENT_FILES[:5]:
            path = self.dest / 'agents' / name
            shutil.copy2(self.source / 'assets/agents' / name, path)
            entries[f'agents/{name}'] = {'kind': 'file', 'sha256': setup.digest(path)}
        receipt = self.dest / 'pstack/install.json'
        receipt.parent.mkdir()
        receipt.write_text(json.dumps({'schema': setup.LEGACY_SCHEMA, 'source': str(old_source), 'entries': entries}))
        return receipt

    def test_legacy_update_moves_entry_and_adds_read_only_reviewers(self):
        old_receipt = self.legacy_install()
        before = old_receipt.read_bytes()
        _, rows, receipt = setup.plan(self.dest, self.source, 'check')
        self.assertTrue(receipt['legacy'])
        self.assertEqual(before, old_receipt.read_bytes())
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'install')
        setup.apply(self.dest, self.source, 'update')
        self.assertFalse(old_receipt.exists())
        self.assertFalse((self.dest / 'skills/pstack').is_symlink())
        self.assertEqual((self.dest / setup.LINK).resolve(), self.source.resolve())
        import tomllib
        for name in ('thermos-correctness.toml', 'thermos-quality.toml'):
            data = tomllib.loads((self.dest / 'agents' / name).read_text())
            self.assertEqual(data['sandbox_mode'], 'read-only')
            self.assertNotIn('model', data)
        self.assertTrue(all(row['state'] == '配置済み' for row in setup.plan(self.dest, self.source, 'check')[1]))

    def test_legacy_update_protects_edited_agents_and_new_name_collisions(self):
        old_receipt = self.legacy_install()
        before = old_receipt.read_bytes()
        existing = self.dest / 'agents/pstack-skeptic.toml'
        existing.write_text(existing.read_text() + '\n# 利用者の変更\n')
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'update')
        self.assertEqual(before, old_receipt.read_bytes())
        self.assertFalse((self.dest / setup.LINK).is_symlink())
        shutil.copy2(self.source / 'assets/agents/pstack-skeptic.toml', existing)
        (self.dest / setup.LINK).mkdir()
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'update')
        self.assertTrue((self.dest / 'skills/pstack').is_symlink())

    def test_legacy_failure_rolls_back_old_link_and_receipt(self):
        from unittest.mock import patch
        old_receipt = self.legacy_install()
        before = old_receipt.read_bytes()
        original = Path.replace
        def fail_receipt(path, target):
            if Path(target) == setup.receipt_path(self.dest):
                raise OSError('移行中の管理記録の書き込み失敗')
            return original(path, target)
        with patch.object(Path, 'replace', fail_receipt):
            with self.assertRaises(OSError):
                setup.apply(self.dest, self.source, 'update')
        self.assertEqual(before, old_receipt.read_bytes())
        self.assertTrue((self.dest / 'skills/pstack').is_symlink())
        self.assertFalse((self.dest / setup.LINK).is_symlink())
        self.assertFalse((self.dest / 'agents/thermos-quality.toml').exists())

    def test_legacy_receipt_cannot_claim_another_source(self):
        import json
        receipt = self.legacy_install()
        data = json.loads(receipt.read_text())
        data['source'] = str(self.base / '他人のpstack')
        receipt.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'update')
        self.assertTrue((self.dest / 'skills/pstack').is_symlink())

    def shared_install(self):
        shared = self.dest / 'skills/dev'
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.symlink_to(self.source.parent, target_is_directory=True)
        return shared

    def test_shared_skill_lifecycle_manages_only_agents(self):
        import json
        shared = self.shared_install()
        original_target = shared.readlink()
        original_skill = (self.source / 'SKILL.md').read_bytes()
        _, rows, receipt = setup.plan(self.dest, self.source, 'check')
        self.assertIsNone(receipt)
        self.assertEqual(len(rows), 7)
        self.assertFalse((self.dest / 'agents').exists())
        setup.apply(self.dest, self.source, 'install')
        self.assertFalse((self.dest / setup.LINK).exists())
        record = json.loads(setup.receipt_path(self.dest).read_text())
        self.assertNotIn(setup.LINK, record['entries'])
        self.assertEqual(len(record['entries']), 7)
        setup.apply(self.dest, self.source, 'install')
        (self.dest / 'agents/thermos-quality.toml').unlink()
        setup.apply(self.dest, self.source, 'install')
        template = self.source / 'assets/agents/thermos-quality.toml'
        template.write_text(template.read_text() + '\n# テンプレートの更新\n')
        setup.apply(self.dest, self.source, 'update')
        self.assertEqual(template.read_bytes(), (self.dest / 'agents/thermos-quality.toml').read_bytes())
        edited = self.dest / 'agents/thermos-correctness.toml'
        edited.write_text(edited.read_text() + '\n# 利用者の変更\n')
        for action in ('update', 'uninstall'):
            with self.assertRaises(ValueError):
                setup.apply(self.dest, self.source, action)
        shutil.copy2(self.source / 'assets/agents/thermos-correctness.toml', edited)
        setup.apply(self.dest, self.source, 'uninstall')
        self.assertEqual(shared.readlink(), original_target)
        self.assertEqual((self.source / 'SKILL.md').read_bytes(), original_skill)
        self.assertFalse((self.dest / setup.LINK).exists())
        self.assertFalse(setup.receipt_path(self.dest).exists())

    def test_preexisting_unowned_direct_link_is_reused_and_preserved(self):
        link = self.dest / setup.LINK
        link.parent.mkdir(parents=True)
        link.symlink_to(self.source)
        setup.apply(self.dest, self.source, 'install')
        setup.apply(self.dest, self.source, 'uninstall')
        self.assertEqual(link.resolve(), self.source.resolve())

    def test_update_retires_only_owned_duplicate_link(self):
        import json
        setup.apply(self.dest, self.source, 'install')
        shared = self.shared_install()
        _, rows, _ = setup.plan(self.dest, self.source, 'check')
        self.assertTrue((self.dest / setup.LINK).is_symlink())
        setup.apply(self.dest, self.source, 'update')
        self.assertFalse((self.dest / setup.LINK).is_symlink())
        self.assertEqual(shared.resolve(), self.source.parent.resolve())
        self.assertNotIn(setup.LINK, json.loads(setup.receipt_path(self.dest).read_text())['entries'])

    def test_shared_skills_directory_is_never_written(self):
        self.dest.mkdir(parents=True)
        shared = self.dest / 'skills'
        shared.symlink_to(self.source.parent)
        before = sorted(p.relative_to(self.source.parent).as_posix() for p in self.source.parent.rglob('*'))
        setup.apply(self.dest, self.source, 'install')
        setup.apply(self.dest, self.source, 'update')
        setup.apply(self.dest, self.source, 'uninstall')
        after = sorted(p.relative_to(self.source.parent).as_posix() for p in self.source.parent.rglob('*'))
        self.assertEqual(before, after)
        self.assertEqual(shared.resolve(), self.source.parent.resolve())

    def test_missing_shared_link_can_be_repaired_or_uninstalled(self):
        shared = self.shared_install()
        setup.apply(self.dest, self.source, 'install')
        shared.unlink()
        setup.apply(self.dest, self.source, 'update')
        self.assertEqual((self.dest / setup.LINK).resolve(), self.source.resolve())
        setup.apply(self.dest, self.source, 'uninstall')
        shared = self.shared_install()
        setup.apply(self.dest, self.source, 'install')
        shared.unlink()
        setup.apply(self.dest, self.source, 'uninstall')
        self.assertFalse((self.dest / setup.LINK).is_symlink())

    def test_shared_entry_from_another_source_stops_before_writes(self):
        foreign = self.base / '別の共通スキル/pstack-thermos'
        foreign.mkdir(parents=True)
        (foreign / 'SKILL.md').write_text('利用者の別スキル')
        shared = self.dest / 'skills/dev'
        shared.parent.mkdir(parents=True)
        shared.symlink_to(foreign.parent)
        with self.assertRaises(ValueError):
            setup.apply(self.dest, self.source, 'install')
        self.assertFalse((self.dest / 'agents').exists())
        self.assertEqual((foreign / 'SKILL.md').read_text(), '利用者の別スキル')

    def test_duplicate_link_retirement_rolls_back_on_receipt_failure(self):
        from unittest.mock import patch
        setup.apply(self.dest, self.source, 'install')
        shared = self.shared_install()
        before = setup.receipt_path(self.dest).read_bytes()
        original = Path.replace
        def fail_receipt(path, target):
            if Path(target) == setup.receipt_path(self.dest):
                raise OSError('入口の整理中に管理記録を書けない試験')
            return original(path, target)
        with patch.object(Path, 'replace', fail_receipt):
            with self.assertRaises(OSError):
                setup.apply(self.dest, self.source, 'update')
        self.assertEqual(setup.receipt_path(self.dest).read_bytes(), before)
        self.assertEqual((self.dest / setup.LINK).resolve(), self.source.resolve())
        self.assertEqual(shared.resolve(), self.source.parent.resolve())

    def test_legacy_update_uses_existing_shared_entry(self):
        import json
        old_receipt = self.legacy_install()
        shared = self.shared_install()
        setup.apply(self.dest, self.source, 'update')
        self.assertFalse(old_receipt.exists())
        self.assertFalse((self.dest / 'skills/pstack').is_symlink())
        self.assertFalse((self.dest / setup.LINK).is_symlink())
        record = json.loads(setup.receipt_path(self.dest).read_text())
        self.assertEqual(len(record['entries']), 7)
        self.assertNotIn(setup.LINK, record['entries'])
        self.assertEqual(shared.resolve(), self.source.parent.resolve())


if __name__ == '__main__':
    unittest.main()
