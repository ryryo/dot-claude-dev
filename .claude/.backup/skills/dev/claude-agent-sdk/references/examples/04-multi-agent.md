# #4 マルチエージェント研究システム（Python）

**何を作れるか**: リードエージェントがタスクを分解し、専門サブエージェント（リサーチャー、データ分析、レポート作成等）に並列で委譲する研究システム。最終的にPDFレポートを自動生成。

**デモソース**: [research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent)

## アーキテクチャ

```
ユーザー → ClaudeSDKClient (リードエージェント)
              ├── Task → researcher (WebSearch, Write)     ← AgentDefinition
              ├── Task → researcher (WebSearch, Write)     ← 並列実行
              ├── Task → data-analyst (Read, Bash, Write)  ← 研究結果を分析
              └── Task → report-writer (Skill, Bash, Write) ← PDF生成
```

**SDK主要機能**: `ClaudeSDKClient`, `AgentDefinition`, `HookMatcher`, `ClaudeAgentOptions`

## コード例: サブエージェント定義（Python）

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AgentDefinition, HookMatcher

# 専門サブエージェントの定義
agents = {
    "researcher": AgentDefinition(
        description=(
            "Use this agent when you need to gather research information. "
            "Uses web search to find relevant articles and sources. "
            "Writes findings to files/research_notes/."
        ),
        tools=["WebSearch", "Write"],
        prompt=researcher_prompt,  # 外部ファイルから読み込み
        model="haiku"
    ),
    "data-analyst": AgentDefinition(
        description=(
            "Use AFTER researchers complete their work. "
            "Reads research notes, extracts data, generates charts via matplotlib."
        ),
        tools=["Glob", "Read", "Bash", "Write"],
        prompt=data_analyst_prompt,
        model="haiku"
    ),
    "report-writer": AgentDefinition(
        description=(
            "Creates formal PDF reports from research findings and charts. "
            "Does NOT conduct web searches."
        ),
        tools=["Skill", "Write", "Glob", "Read", "Bash"],
        prompt=report_writer_prompt,
        model="haiku"
    ),
}
```

## コード例: フック付きクライアント起動（Python）

```python
# フックでサブエージェントのツール呼び出しを追跡
tracker = SubagentTracker(transcript_writer=transcript, session_dir=session_dir)

hooks = {
    'PreToolUse': [
        HookMatcher(
            matcher=None,  # 全ツールにマッチ
            hooks=[tracker.pre_tool_use_hook]
        )
    ],
    'PostToolUse': [
        HookMatcher(
            matcher=None,
            hooks=[tracker.post_tool_use_hook]
        )
    ],
}

# リードエージェントの構成
options = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    setting_sources=["project"],      # プロジェクトの .claude/ からスキルを読み込み
    system_prompt=lead_agent_prompt,
    allowed_tools=["Task"],           # リードエージェントは Task のみ（委譲専用）
    agents=agents,                    # サブエージェント定義を渡す
    hooks=hooks,
    model="haiku"
)

# インタラクティブセッション
async with ClaudeSDKClient(options=options) as client:
    while True:
        user_input = input("You: ").strip()
        await client.query(prompt=user_input)

        async for msg in client.receive_response():
            if type(msg).__name__ == 'AssistantMessage':
                process_assistant_message(msg, tracker, transcript)
```

## コード例: サブエージェント追跡（フック実装, Python）

```python
class SubagentTracker:
    """PreToolUse/PostToolUse フックでサブエージェントのツール呼び出しを追跡"""

    async def pre_tool_use_hook(self, hook_input, tool_use_id, context):
        tool_name = hook_input['tool_name']
        tool_input = hook_input['tool_input']

        is_subagent = (self._current_parent_id
                       and self._current_parent_id in self.sessions)

        if is_subagent:
            session = self.sessions[self._current_parent_id]
            self._log_tool_use(session.subagent_id, tool_name, tool_input)
            # JSONL形式で詳細ログ出力
            self._log_to_jsonl({
                "event": "tool_call_start",
                "agent_id": session.subagent_id,
                "tool_name": tool_name,
                "tool_input": tool_input,
            })

        return {'continue_': True}  # ツール実行を許可

    async def post_tool_use_hook(self, hook_input, tool_use_id, context):
        tool_response = hook_input.get('tool_response')
        record = self.tool_call_records.get(tool_use_id)
        if record:
            record.tool_output = tool_response
        return {'continue_': True}
```

## ポイント

- `AgentDefinition` で各サブエージェントの責務・ツール・モデルを宣言的に定義
- リードエージェントは `allowed_tools=["Task"]` のみで委譲専用に設計
- `HookMatcher(matcher=None)` で全ツールの呼び出しをインターセプト
- サブエージェントのプロンプトは外部ファイル化して管理
- `setting_sources=["project"]` でプロジェクトの `.claude/skills/` を活用
- 各サブエージェントに最適なモデルサイズを指定してコスト最適化
