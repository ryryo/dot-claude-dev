#!/usr/bin/env python3
"""単一の入口、内部手順、参照先、出典、担当設定を検査する。"""
from pathlib import Path
import hashlib
import json
import re
import sys
import tomllib
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
JAPANESE = re.compile(r'[ぁ-んァ-ヶ一-龯]')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visible(text):
    text = re.sub(r'^---\n[\s\S]*?\n---\n', '', text)
    return re.sub(r'(?m)^(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\s*$', '', text)


def validate(root=ROOT):
    errors = []
    provenance = json.loads((root/'provenance.json').read_text())
    adaptations = provenance['code_adaptations']
    for group in ('upstream_files', 'local_previous_files', 'thermos_files'):
        for item in provenance[group]:
            destination = item['destination']
            if destination is None:
                if group == 'upstream_files' and not item.get('omitted_reason'):
                    errors.append(f"省いた理由がありません: {item['path']}")
                continue
            path = root/destination
            if not path.is_file():
                errors.append(f"移行先がありません: {item['path']} -> {destination}")
                continue
            historical = destination.startswith('provenance/pstack/validation/') or (group == 'local_previous_files' and destination.startswith('provenance/'))
            preserved = path.suffix in ('.py', '.sh', '.mjs', '.ts') or path.name == 'LICENSE' or historical
            if preserved and destination not in adaptations and digest(path) != item['sha256']:
                errors.append(f"保持するコード・ライセンス・過去証拠に変更があります: {destination}")

    skills = [p.relative_to(root).as_posix() for p in root.rglob('SKILL.md')
              if not any(x in p.parts for x in ('node_modules', '__pycache__'))]
    if skills != ['SKILL.md']:
        errors.append(f"スキルの入口は一つに限ります: {skills}")
    metadata = [p.relative_to(root).as_posix() for p in root.rglob('openai.yaml')]
    if metadata != ['agents/openai.yaml']:
        errors.append(f"UI設定が複数あります: {metadata}")
    if any(root.rglob('plugin.json')) or any(root.rglob('marketplace.json')):
        errors.append('個別プラグインの定義が残っています')
    frontmatter = re.match(r'^---\n([\s\S]*?)\n---\n', (root/'SKILL.md').read_text())
    if not frontmatter or not re.search(r'^name: pstack-thermos$', frontmatter[1], re.M) or not re.search(r'^description: .+', frontmatter[1], re.M):
        errors.append('入口のメタデータが不正です')

    procedures = list((root/'references/pstack').glob('*/guide.md'))
    playbooks = list((root/'references/pstack/poteto-mode/playbooks').glob('*.md'))
    if len(procedures) != 54 or len(playbooks) != 23:
        errors.append(f"収録数が違います: {len(procedures)}内部手順、{len(playbooks)}作業手順")
    index = (root/'references/pstack/index.md').read_text()
    for path in procedures:
        relative = path.relative_to(root/'references/pstack').as_posix()
        if f']({relative})' not in index:
            errors.append(f"内部手順の索引にありません: {relative}")
        if path.read_text().startswith('---\n'):
            errors.append(f"内部手順にスキルのメタデータが残っています: {relative}")
    for name in ('guide.md', 'correctness.md', 'code-quality.md', 'report.md'):
        if not (root/'references/thermos'/name).is_file():
            errors.append(f"thermosの手順がありません: {name}")

    docs = [p for p in root.rglob('*.md') if not any(x in p.parts for x in ('node_modules', '__pycache__'))
            and 'provenance' not in p.relative_to(root).parts and p.name != 'plan-upstream.md']
    for path in docs:
        text = visible(path.read_text())
        if not JAPANESE.search(text):
            errors.append(f"日本語の本文がありません: {path.relative_to(root)}")
        for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', link) or '<' in link:
                continue
            target = unquote(link.split('#')[0].split(' "')[0])
            if target and not (path.parent/target).exists():
                errors.append(f"参照先がありません: {path.relative_to(root)} -> {link}")

    agents = list((root/'assets/agents').glob('*.toml'))
    if len(agents) != 7:
        errors.append('担当設定は7種類必要です')
    names = set()
    for path in agents:
        data = tomllib.loads(path.read_text())
        name = data.get('name')
        if not name or name in names:
            errors.append(f"担当名が不正または重複しています: {path.name}")
        names.add(name)
        for field in ('description', 'developer_instructions'):
            if not JAPANESE.search(data.get(field, '')):
                errors.append(f"担当の日本語指示がありません: {path.name}/{field}")
        if 'model' in data or 'model_reasoning_effort' in data:
            errors.append(f"初回のモデル継承を変えています: {path.name}")
        if path.name != 'poteto-agent.toml' and data.get('sandbox_mode') != 'read-only':
            errors.append(f"レビュー担当が読み取り専用ではありません: {path.name}")
    if not {'thermos_correctness', 'thermos_quality'} <= names:
        errors.append('thermosの二担当がありません')
    return errors, len(docs)


if __name__ == '__main__':
    errors, count = validate()
    for error in errors:
        print(error, file=sys.stderr)
    print(f"構成の検査: 1スキル、54内部手順、23作業手順、7担当、{count}文書、問題{len(errors)}件")
    sys.exit(bool(errors))
