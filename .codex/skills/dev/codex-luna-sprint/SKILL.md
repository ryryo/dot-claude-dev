---
name: codex-luna-sprint
description: "main Codexが判断・契約・統合・最終検収を保持し、固定済みまたはboundedな軽量実装、純粋ロジック、behavior test、局所UI leaf、read-heavy調査をGPT-5.6 Luna mediumのCustom Agentへ委任する。排他的write scope、再現可能なoracle、可逆なlocal diffを持つtaskを短いSprintとして実行する。Trigger: codex-luna-sprint、Luna worker sprint、Custom Agentで実装、安価なCodex subagentへ委任、Cursor workerをLunaへ置換。"
---

# Codex Luna Sprint

GPT-5.6 Lunaの`luna_sprint_worker`へ、明確で反復可能なleaf taskだけを委任する。main Codexはsource of truth、判断、共有contract、diff検収、統合、外部副作用、最終完了判定を所有する。

## 実行者を決める

最初はすべてmain Codex担当とし、次をすべて満たすtaskだけLunaへ移す。

1. expected behavior、contract、invariant、禁止事項がfixedまたはbounded。
2. task-local contextだけで完結するか、main Gate後に独立する。
3. write scopeが他のmain／user／workerと重ならない。
4. focused test、fixture、typecheck、build、snapshot等のoracleがstrongまたは限定可能なpartial。
5. local diffとして棄却でき、外部stateを変更しない。
6. 既存pattern、test、fixture、参照実装のいずれかを直接使える。

architecture、product、security、data ownership、shared schema、auth、secret、crypto、課金、production、deploy、実provider、最終UX判断、最終acceptanceはmain Codexが扱う。分割と検収の負担が実装より大きい場合もmainが一貫して扱う。

## Custom Agent

既定agentは個人スコープの`~/.codex/agents/luna-sprint-worker.toml`にある`luna_sprint_worker`とする。モデルは`gpt-5.6-luna`、reasoningは`medium`固定。この名前付きCustom Agentをnative subagentとして選択できる環境でだけ委任する。

task開始前に、現在のcollaboration toolが`luna_sprint_worker`またはCustom Agent profileの選択を公開しているか確認する。選択できない場合は、CLIを別経路で起動せず、そのtaskをmain Codexへ戻すか、新しいsessionでCustom Agentが公開されるまで停止する。Terra、Sol、Cursorへ黙って置換しない。

疎通確認専用のtaskは通常作らない。最初の実taskをspawnし、agent選択自体が失敗した場合だけ追加投入を止めて利用不能として扱う。

## Sprintを初期化する

```bash
LUNA_WORKSPACE="$(pwd)"
LUNA_SKILL_DIR="$(cd "$LUNA_WORKSPACE/.codex/skills/dev/codex-luna-sprint" && pwd)"
"$LUNA_SKILL_DIR/scripts/init_sprint.sh" \
  --workspace "$LUNA_WORKSPACE" \
  --slug "<short-slug>"
. "$LUNA_WORKSPACE/.codex/tmp/$(date +%y%m%d)_<short-slug>/sprint-env.sh"
```

作成物:

```text
.codex/tmp/YYMMDD_slug/
  brief.md
  tasks.md
  prompts/
  review.md
  sprint-env.sh
```

`brief.md`へ目的、範囲、repository context、制約、最小検証を書く。`tasks.md`へ依存、担当、read／write scope、競合、oracle、受入条件を書く。永続計画、Gate、commit、pushはmainだけが更新する。

## Task contractを作る

taskごとに`prompts/Txx.md`を1つ作る。詳細templateは[task-contract.md](references/task-contract.md)を読む。必須項目:

- `Task Summary:`: 180文字以内でtaskごとに一意。
- `Task ID:`: registryとreportを対応させるID。
- fixed／bounded decision、independence、side effect、oracle。
- 絶対pathのread scopeと排他的write scope。
- forbidden changesとmainへ戻す条件。
- worker verificationとmain verification。

workerにcommit、push、PR、branch変更、計画更新、外部API実行、実secret使用、allowed scope外変更、別agentへの再委任を許可しない。

## 実行する

現在のcollaboration toolで`luna_sprint_worker`を明示してnative subagentをspawnする。`prompts/Txx.md`の全文をtaskとして渡し、同時実行はwrite scopeが重ならないtaskだけにする。実行中の追跡、interrupt、follow-upはnative subagent機能を使う。

agentの選択肢に`luna_sprint_worker`がない、またはspawn時に利用不能と判明した場合は次のいずれかに限定する。

1. taskを`main-codex`へ戻してmainが実装する。
2. 新しいsessionでCustom Agentが公開された後に再開する。

独自runner、headless CLI、background process、model上書きによる代替起動は作らない。mainはagentの報告だけでなく共有workspaceの実diffを検収する。

## mainが検収する

worker完了後に必ず確認する。

```bash
git status --short
git diff --name-only
git diff --stat
git diff -- <allowed-paths>
```

確認事項:

- diffがallowed scope内で、既存変更を戻していない。
- reportと実diffが一致する。
- fixed／bounded contractを勝手に変更していない。
- worker testをmainが再実行できる。
- risk modifierのnegative caseが通る。
- ユーザー視点の振る舞いが成立する。

検収後だけtaskをacceptedにし、依存順に統合する。UIは可能ならbrowserでも確認する。Sprintの結果と補正は`review.md`へ記録する。

## 完了報告

次だけを短く報告する。

- Sprint directory
- `luna_sprint_worker`を使ったtaskとmainへ戻したtask
- 変更ファイル
- worker検証とmain再検証
- 棄却・補正した内容
- 残リスクと次のtask
