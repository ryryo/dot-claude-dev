---
name: parallel-agent-brief
description: |
  低〜中複雑度で独立性の高い実装・調査・テスト作業を、複数の外部エージェントへ並列委任するためのコピペ可能な指示書に分解する。
  docs/PLAN の Gate/Todo、spec-codex-run、参照実装、既存コードを読み、衝突しにくい担当範囲・禁止事項・検証条件を含む依頼文を作る。
  Trigger: 並列エージェント指示書, 他エージェントに投げる, 低複雑度タスクを分担, コピペ用プロンプト, parallel agent brief, delegate simple tasks
---

# 並列エージェント指示書

低〜中複雑度の作業を、並列実装が得意なエージェントへ安全に渡すための指示書を作る。目的は実装そのものではなく、衝突しにくい作業単位、参照すべき仕様、編集禁止範囲、完了条件を明確にしたコピペ用プロンプトを出力すること。

## 原則

- まず事実確認する。存在しないパス、未確認のスキル、未読の計画ファイルを前提にしない。
- 低複雑度の独立タスクだけを切り出す。共有 UI shell、共通 state、export pipeline、最終統合、Gate PASS 判定は原則メイン側に残す。
- 並列作業者には期待する結論を渡さない。生のパス、契約、担当範囲、検証条件を渡す。
- 複数エージェントが同じファイルを編集しないよう、write scope を明示する。
- docs/PLAN の状態更新、`spec.md` 同期、コミット、push は、ユーザーが明示しない限り委任プロンプトに含めない。
- 既存の未コミット変更はユーザーまたは他エージェントの作業として扱い、巻き戻し禁止を明記する。

## Step 1: 参照元を確認する

作業前に、ユーザーが指定したスキル、計画ファイル、参照実装、対象ディレクトリが実在するか確認する。

- `find`、`rg --files`、`ls -l`、`realpath` を使い、symlink も確認する。
- `.codex/skills/dev/spec-codex-run/SKILL.md` や `.claude/skills/dev/spec-run/SKILL.md` など、同名・類似スキルが複数ある場合は、実在パスを出力に明記する。
- `docs/PLAN/{YYMMDD}_{slug}/tasks.json` がある場合は `tasks.json` を正とし、`spec.md` は補助または生成物として扱う。
- 参照実装がある場合は、委任タスクごとに読むべき参照パスを明示する。

## Step 2: タスクを複雑性で分類する

委任候補を以下に分類する。

低複雑度:
- 純粋関数、helper、schema、validator、単体テスト。
- 新規小ディレクトリに閉じる実装。
- UI や共通 state への接続が不要、または adapter 境界だけで完結する。
- 入出力と検証条件が明確。

中複雑度:
- 小さな UI 部品、既存 helper への接続、限定的な storage/permission 連携。
- 先行 task の成果に依存するが、write scope を分けられる。

高複雑度:
- 共通 state、editor/canvas、export pipeline、routing、最終統合、実ブラウザ検証、Gate PASS 更新。
- 複数 Gate にまたがる振る舞い。
- 仕様の曖昧さが残るもの。

高複雑度は「メイン側で保持」または「調査のみ委任」として扱う。

## Step 3: 委任単位を設計する

各委任単位に次を定義する。

- 目的: 何を完成させるか。
- 参照: 読むべき skill、`docs/PLAN`、参照実装、既存コード。
- 担当ファイル: 変更してよいパス。可能ならディレクトリ単位で分離する。
- 範囲外: 触ってはいけないファイル、Gate 状態更新、コミット、統合 UI など。
- 完了条件: テスト、typecheck、build、成果報告の形式。
- 報告事項: 変更ファイル、対応 Gate/Todo/AC、検証結果、残課題。

`docs/PLAN` がある場合は、各プロンプトに次を入れる。

```text
まず /absolute/path/to/.codex/skills/dev/spec-codex-run/SKILL.md を読んでください。
次に /absolute/path/to/docs/PLAN/{YYMMDD}_{slug}/tasks.json を読み、対象 Gate/Todo/AC だけを契約として扱ってください。
tasks.json が正です。spec.md は補助または生成物です。
並行作業前提なので docs/PLAN/{YYMMDD}_{slug}/tasks.json と spec.md は編集しないでください。
```

## Step 4: コピペ用プロンプトを作る

出力は、共通前提プロンプト 1 つと、Agent ごとの個別プロンプトに分ける。

共通前提には必ず含める。

- 作業場所。
- 読むべき skill と計画ファイルの絶対パス。
- 並行作業前提の禁止事項。
- 既存変更を戻さないこと。
- コミットしないこと。
- 完了報告フォーマット。

個別プロンプトには必ず含める。

- Agent 名または担当名。
- 対象 Gate/Todo/AC。
- 担当ファイル。
- 実装範囲。
- 範囲外。
- 検証コマンド。
- 完了時に報告する内容。

## 出力テンプレート

```text
共通前提:
作業場所: <absolute workspace path>

まず次を読んでください:
- <absolute path to relevant skill, e.g. .codex/skills/dev/spec-codex-run/SKILL.md>
- <absolute path to docs/PLAN/.../tasks.json>
- 必要に応じて <absolute path to docs/PLAN/.../spec.md>

重要:
- tasks.json が正です。spec.md は補助または生成物として扱ってください。
- 並行作業前提なので、docs/PLAN/.../tasks.json と spec.md は編集しないでください。
- 自分に割り当てられたファイルだけを変更してください。
- 他エージェントの変更、既存未コミット変更、対象外ディレクトリを戻さないでください。
- コミットや push はしないでください。
- 完了時は、変更ファイル、対応 Gate/Todo/AC、実行した検証コマンド、残課題を報告してください。

検証の基本:
cd <project subdir if needed>
<typecheck command>
<test command>
必要なら <build command>
```

```text
Agent <name>: <task title>

目的:
<what this agent should complete>

参照:
- <tasks.json Gate/Todo/AC>
- <reference implementation paths if any>
- <existing implementation paths>

担当ファイル:
- <path>
- <path>

実装範囲:
- <bullet>
- <bullet>

範囲外:
- <bullet>
- docs/PLAN の更新
- コミット / push

完了条件:
- <test or verification>
- <reporting expectation>
```

## 最終チェック

出力前に確認する。

- 実在確認したパスだけを書いている。
- 各 Agent の write scope が重複していない、または重複リスクを明記している。
- 高複雑度の統合作業を低複雑度タスクとして投げていない。
- `docs/PLAN` の更新権限が曖昧ではない。
- 検証コマンドがプロジェクトに存在する。
- 報告フォーマットがあり、統合側が成果を受け取りやすい。
