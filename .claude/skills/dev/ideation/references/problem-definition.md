# 問題定義仕様（problem-definition）

ユーザーのアイデアをJTBDフレームワークで分析し、問題定義を構造化する。

## 手順

1. JTBDフレームワーク（references/jtbd-framework.md）を参照する
2. アイデアから以下を抽出する:
   - ターゲットユーザー（誰の問題か）
   - コアジョブ（何を達成したいか）
   - 現在の代替手段（今どうしているか）
3. 3層のJTBD分析を行う:
   - Functional Job（機能的ジョブ）
   - Emotional Job（感情的ジョブ）
   - Social Job（社会的ジョブ）
4. ペイン/ゲイン分析を行う:
   - 現在の代替手段のペイン（優先度付き）
   - 理想的な解決策のゲイン（優先度付き）
5. AskUserQuestion で深掘りする:
   - 「このペインの中で最も深刻なものはどれですか？」
   - 「ターゲットユーザーの認識は合っていますか？」

## 出力構造

init スクリプトで配置済みの `{dir}/PROBLEM_DEFINITION.md` を Read し、各セクションの内容を埋めて Write で上書きする。

## 完了条件

- `{dir}/PROBLEM_DEFINITION.md` が保存されている
- JTBDの3層が記載されている
- ペイン/ゲインに優先度が付いている
