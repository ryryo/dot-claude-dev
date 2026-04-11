# worktree 終了処理（spec-run 用）

全 Gate 通過 + 人間レビュー OK 後に実行する。worktree を master にマージし cleanup する。

## 前提

- `$MASTER_ROOT`: setup 前に `MASTER_ROOT="$(pwd)"` で保存済み
- `$WORKTREE_PATH`: setup 時に stdout から記憶済み
- `{slug}`: 仕様書ファイル名から拡張子を除いたもの
- cleanup-worktree.sh は `.claude/skills/dev/spec-run/scripts/` に配置済み

---

## フェーズ 5: 完了時 merge

1. `git -C "$WORKTREE_PATH" status --porcelain` が空であることを確認（非空なら先にコミット）
2. **master ルートに cwd を戻す**: `cd "$MASTER_ROOT"`
3. base ブランチを検出: `git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'`（フォールバックは master → main）
4. `git checkout {base}`
5. `git pull --ff-only 2>/dev/null || echo "pull skipped (offline or diverged)"` を試行（失敗は警告のみ、続行）
6. `git merge --no-ff feature/{slug} -m "Merge feature/{slug} via spec-run"` を実行
7. 終了コードで分岐:
   - 0: 成功 → フェーズ 6 へ
   - 非 0: コンフリクト → 「コンフリクト自動解決」セクションへ

### コンフリクト自動解決

Claude が `git status --porcelain` で conflict ファイル一覧を取得し、各ファイルに対して以下を判断する:

#### 自動解決 OK

| パターン | 判定方法 | 解決 |
|---------|---------|------|
| import 文の順序のみの差異 | diff が import 系の行のみに限定 | 両方の import を union、重複除去 |
| コメント・空白のみの差異 | diff が `//` / `#` / 空白のみ | 両方残す（実害なし） |
| 片側が完全な superset | 一方の変更が他方を完全に含む | superset 側を採用 |
| spec.md の同一チェックボックス行、両側 `[x]` | `- [x]` が両側 | `[x]` を採用 |
| spec.md の同一チェックボックス行、片側のみ `[x]` | 片側 `[x]`、片側 `[ ]` | `[x]` を採用（進捗優先） |

#### AskUserQuestion でエスカレーション

- 同じ関数のロジックが両側で変更
- spec.md の Review blockquote 内容が両側変更
- package.json / tsconfig.json 等の設定ファイル両側変更
- .env 系のファイル
- 上記パターンに当てはまらない全てのコンフリクト

エスカレーション時の選択肢:
1. ユーザーが手動解決 → 解決後に「完了」報告を待つ
2. 特定ファイルを master 側で上書き（`git checkout --theirs <file>`）
3. 特定ファイルを worktree 側で上書き（`git checkout --ours <file>`）
4. merge を abort（`git merge --abort`）して spec-run を停止

自動解決後は `git add <files> && git commit --no-edit` でマージを完了させる。

---

## フェーズ 6: cleanup

1. cwd は master リポジトリルート（フェーズ 5 で切り替え済み）
2. `bash .claude/skills/dev/spec-run/scripts/cleanup-worktree.sh {slug}` を実行
3. 終了コードで分岐:
   - 0: 成功 → 完了処理の残りへ
   - 2: worktree 削除失敗（未コミット変更残留 or git worktree remove 失敗）→ stderr をユーザーに報告して中断
   - 3: feature ブランチ削除失敗（未マージ）→ ユーザーに状況確認を依頼。merge が実際に成功していたか確認（merge commit の存在確認）

### Codex モード特有

- worktree 内の `.tmp/codex-*.md` は cleanup-worktree.sh で worktree ごと消える
- master 側に `.tmp/codex-*.md` が残っていれば削除する（`rm -f .tmp/codex-*.md`）

---

## フェーズ 7: エラーリカバリ

### reuse 時マージ失敗（セットアップ時）
- ユーザーが「abort」を選んだ場合: `git merge --abort` → spec-run 停止。worktree は残る（次回セッションで再 reuse 可能）

### Gate 実行失敗
- 既存 spec-run の FIX ループに従う（worktree 特有の処理なし）
- 3 ラウンド超過したら既存プロトコル通りユーザーに判断を仰ぐ
- spec-run 中断時は worktree を残して終了（次回セッションで reuse）

### 完了時マージ失敗（フェーズ 5）
- フェーズ 5 のコンフリクト自動解決ロジックを適用
- 解決不能な場合は spec-run を停止、worktree と feature ブランチは残す（次回 reuse の選択肢をユーザーに残す）
- この時点で cwd は master にいるので、ユーザーは手動で `git merge --abort` や `git reset` で状態を戻せる

### cleanup 失敗（フェーズ 6）
- exit 2 / 3 の内容をユーザーに報告
- 自動リトライは行わない（状態破壊を避けるため）
- ユーザーは `.claude/skills/dev/cleanup-branches/` スキルを使って手動整理可能
