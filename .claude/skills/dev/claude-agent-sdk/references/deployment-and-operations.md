# Deployment & Operations - Claude Agent SDK

本ドキュメントは、Claude Agent SDKのデプロイメント、セキュリティ、コスト追跡に関する設計判断のためのリファレンスです。

---

## 1. ホスティングとデプロイメント

### SDKアーキテクチャの特性

Claude Agent SDKは従来のステートレスなLLM APIとは異なり、**長時間実行プロセス**として動作する:

- 永続的なシェル環境でコマンドを実行する
- 作業ディレクトリ内でファイル操作を管理する
- 以前のインタラクションからのコンテキストを使用してツール実行を処理する

### システム要件

| カテゴリ | 要件 |
|---------|------|
| ランタイム | Python 3.10+（Python SDK）またはNode.js 18+（TypeScript SDK） |
| CLI | Node.js必須、`npm install -g @anthropic-ai/claude-code` |
| リソース | 推奨: 1GiB RAM、5GiBディスク、1 CPU（タスクに応じて調整） |
| ネットワーク | `api.anthropic.com`へのアウトバウンドHTTPS、オプションでMCPサーバー/外部ツール |

### サンドボックスプロバイダー

| プロバイダー | 特徴 |
|-------------|------|
| [Modal Sandbox](https://modal.com/docs/guide/sandbox) | [デモ実装](https://modal.com/docs/examples/claude-slack-gif-creator)あり |
| [Cloudflare Sandboxes](https://github.com/cloudflare/sandbox-sdk) | - |
| [Daytona](https://www.daytona.io/) | - |
| [E2B](https://e2b.dev/) | - |
| [Fly Machines](https://fly.io/docs/machines/) | - |
| [Vercel Sandbox](https://vercel.com/docs/functions/sandbox) | - |

セルフホストオプション: Docker、gVisor、Firecracker

### 本番デプロイメントパターン

#### パターン1: エフェメラルセッション

各ユーザータスクごとに新しいコンテナを作成し、完了時に破棄する。

**適用例:** バグ調査と修正、請求書処理、翻訳タスク、画像/動画処理

#### パターン2: 長時間実行セッション

永続的なコンテナインスタンスを維持し、需要に応じてコンテナ内で複数のClaude Agentプロセスを実行する。

**適用例:** メールエージェント、サイトビルダー（ライブ編集機能付き）、高頻度チャットボット（Slack等）

#### パターン3: ハイブリッドセッション

データベースまたはSDKのセッション再開機能から履歴と状態をハイドレートするエフェメラルコンテナ。断続的なインタラクションで作業を開始し、完了時にスピンダウンするが継続可能。

**適用例:** パーソナルプロジェクトマネージャー、ディープリサーチ、カスタマーサポートエージェント

#### パターン4: シングルコンテナ

1つのグローバルコンテナ内で複数のClaude Agent SDKプロセスを実行する。エージェント同士が密接に連携する必要がある場合向け。最も一般的でないパターン。

**適用例:** シミュレーション（ビデオゲームなどで互いにインタラクションするエージェント）

### サンドボックスとの通信

コンテナでホスティングする場合、SDKインスタンスと通信するためにポートを公開する。アプリケーションは外部クライアント向けにHTTP/WebSocketエンドポイントを公開でき、SDKはコンテナ内部で実行される。

### セッション管理

- エージェントセッションはタイムアウトしない
- `maxTurns`プロパティの設定を推奨（Claudeのループ防止）
- アイドルタイムアウトはプロバイダー依存（ユーザー応答頻度に基づいて調整）

### コンテナコスト

主要なコストはトークン。コンテナのコストはプロビジョニング内容により異なるが、最小コストは実行時間あたり約5セント。

---

## 2. セキュアデプロイメント

### 脅威モデル

エージェントはプロンプトインジェクション（処理するコンテンツに埋め込まれた指示）やモデルエラーにより意図しないアクションを実行する可能性がある。

### セキュリティ原則

| 原則 | 説明 |
|------|------|
| セキュリティ境界 | 機密リソース（認証情報等）をエージェント境界の外側に配置。プロキシパターンでAPIキーを注入 |
| 最小権限 | エージェントを特定タスクに必要な機能のみに制限 |
| 多層防御 | コンテナ分離 + ネットワーク制限 + ファイルシステム制御 + プロキシでのリクエスト検証 |

### 最小権限のリソース制限オプション

| リソース | 制限方法 |
|---------|---------|
| ファイルシステム | 必要なディレクトリのみをマウント、読み取り専用を推奨 |
| ネットワーク | プロキシ経由で特定のエンドポイントに制限 |
| 認証情報 | 直接公開するのではなくプロキシ経由で注入 |
| システム機能 | コンテナ内でLinux capabilityを削除 |

### 組み込みセキュリティ機能

- **権限システム**: ツールとbashコマンドを許可/ブロック/承認要求に設定。globパターン対応
- **静的解析**: bashコマンド実行前に潜在的にリスクのある操作を特定
- **Web検索の要約**: 生のコンテンツではなく要約でプロンプトインジェクションリスクを軽減
- **サンドボックスモード**: ファイルシステムとネットワークアクセスを制限

### 分離技術の比較

| 技術 | 分離強度 | パフォーマンスオーバーヘッド | 複雑さ |
|------|---------|--------------------------|--------|
| サンドボックスランタイム | 良好（安全なデフォルト） | 非常に低い | 低い |
| コンテナ（Docker） | セットアップに依存 | 低い | 中程度 |
| gVisor | 優秀（正しいセットアップの場合） | 中/高 | 中程度 |
| VM（Firecracker、QEMU） | 優秀（正しいセットアップの場合） | 高い | 中/高 |

#### サンドボックスランタイム

[sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime)はOSレベルでファイルシステムとネットワークの制限を適用する軽量な分離手段。Docker設定、コンテナイメージ、ネットワーク設定は不要。

```
npm install @anthropic-ai/sandbox-runtime
```

**仕組み:**
- **ファイルシステム**: OSプリミティブ（Linuxでは`bubblewrap`、macOSでは`sandbox-exec`）で読み取り/書き込みアクセスを制限
- **ネットワーク**: ネットワーク名前空間を削除（Linux）またはSeatbeltプロファイル使用（macOS）、トラフィックを組み込みプロキシ経由でルーティング
- **設定**: ドメインとファイルシステムパスのJSON形式の許可リスト

**セキュリティに関する考慮事項:**
1. **同一ホストカーネル**: サンドボックス化されたプロセスはホストカーネルを共有。カーネルレベルの分離が必要な場合はgVisorまたは別のVMを使用
2. **TLSインスペクションなし**: プロキシはドメインを許可リストに登録するが暗号化されたトラフィックは検査しない

#### セキュリティ強化されたDockerコンテナ設定

```
docker run \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --security-opt seccomp=/path/to/seccomp-profile.json \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /home/agent:rw,noexec,nosuid,size=500m \
  --network none \
  --memory 2g \
  --cpus 2 \
  --pids-limit 100 \
  --user 1000:1000 \
  -v /path/to/code:/workspace:ro \
  -v /var/run/proxy.sock:/var/run/proxy.sock:ro \
  agent-image
```

| オプション | 目的 |
|-----------|------|
| `--cap-drop ALL` | `NET_ADMIN`や`SYS_ADMIN`等のLinux capabilityを削除 |
| `--security-opt no-new-privileges` | setuidバイナリを通じた権限取得を防止 |
| `--security-opt seccomp=...` | 利用可能なsyscallを制限 |
| `--read-only` | ルートファイルシステムを不変に |
| `--tmpfs /tmp:...` | コンテナ停止時にクリアされる書き込み可能な一時ディレクトリ |
| `--network none` | 全ネットワークインターフェースを削除、Unixソケット経由で通信 |
| `--memory 2g` | メモリ使用量を制限 |
| `--pids-limit 100` | フォーク爆弾を防止 |
| `--user 1000:1000` | 非rootユーザーとして実行 |
| `-v ...:/workspace:ro` | コードを読み取り専用でマウント |
| `-v .../proxy.sock:...` | プロキシへのUnixソケットをマウント |

**追加の強化オプション:**

| オプション | 目的 |
|-----------|------|
| `--userns-remap` | コンテナのrootを非特権ホストユーザーにマッピング |
| `--ipc private` | プロセス間通信を分離 |

#### gVisor

システムコールをホストカーネルに到達する前にユーザースペースでインターセプトする。カーネルエクスプロイトの攻撃対象面を大幅に縮小。

```
// /etc/docker/daemon.json
{
  "runtimes": {
    "runsc": {
      "path": "/usr/local/bin/runsc"
    }
  }
}
```

```
docker run --runtime=runsc agent-image
```

**パフォーマンス特性:**

| ワークロード | オーバーヘッド |
|-------------|--------------|
| CPU集約型の計算 | 約0% |
| 単純なsyscall | 約2倍遅い |
| ファイルI/O集約型 | 頻繁なopen/closeパターンで最大10-200倍遅い |

#### 仮想マシン（Firecracker）

CPU仮想化拡張機能を通じてハードウェアレベルの分離を提供。Firecrackerは125ms未満でVM起動、メモリオーバーヘッド5 MiB未満。`vsock`（仮想ソケット）を通じてホスト上のプロキシと通信。

### クラウドデプロイメント

1. インターネットゲートウェイのないプライベートサブネットでエージェントコンテナを実行
2. クラウドファイアウォールルール（AWS Security Groups、GCP VPCファイアウォール）でプロキシ以外へのエグレスをブロック
3. プロキシ（`credential_injector`フィルターを備えた[Envoy](https://www.envoyproxy.io/)等）でリクエスト検証・ドメイン許可リスト適用・認証情報注入
4. エージェントのサービスアカウントに最小限のIAM権限を割り当て
5. プロキシで全トラフィックをログ記録

### 認証情報管理

#### プロキシパターン（推奨）

エージェントのセキュリティ境界の外側でプロキシを実行し、送信リクエストに認証情報を注入する。

**利点:**
1. エージェントは実際の認証情報を見ることがない
2. プロキシは許可されたエンドポイントの許可リストを適用できる
3. プロキシは監査のためにすべてのリクエストをログ記録できる
4. 認証情報は1つの安全な場所に保存される

#### プロキシ設定方法

**オプション1: ANTHROPIC_BASE_URL（サンプリングAPIリクエストのみ）**

```
export ANTHROPIC_BASE_URL="http://localhost:8080"
```

プロキシはプレーンテキストのHTTPリクエストを受信し、検査・変更（認証情報の注入を含む）してからAPIに転送。

**オプション2: HTTP_PROXY / HTTPS_PROXY（システム全体）**

```
export HTTP_PROXY="http://localhost:8080"
export HTTPS_PROXY="http://localhost:8080"
```

すべてのHTTPトラフィックをプロキシ経由でルーティング。HTTPSの場合、暗号化されたCONNECTトンネルを作成（TLSインターセプションなしではリクエスト内容の変更不可）。

**注意:** すべてのプログラムが`HTTP_PROXY`/`HTTPS_PROXY`を尊重するわけではない。Node.jsの`fetch()`はデフォルトで無視（Node 24以降では`NODE_USE_ENV_PROXY=1`で有効化可能）。包括的なカバレッジには[proxychains](https://github.com/haad/proxychains)またはiptablesを使用。

#### プロキシ実装の選択肢

| プロキシ | 特徴 |
|---------|------|
| [Envoy Proxy](https://www.envoyproxy.io/) | `credential_injector`フィルター、本番グレード |
| [mitmproxy](https://mitmproxy.org/) | TLS終端、HTTPSトラフィックの検査・変更 |
| [Squid](http://www.squid-cache.org/) | ACL付きキャッシングプロキシ |
| [LiteLLM](https://github.com/BerriAI/litellm) | LLMゲートウェイ、認証情報注入・レート制限 |

#### 他サービスの認証情報: カスタムツール方式

MCPサーバーまたはカスタムツールを通じてアクセスを提供。エージェントはツールを呼び出すが、実際の認証済みリクエストは境界の外側で行われる。

**利点:** TLSインターセプション不要、認証情報は外側に留まる

#### 他サービスの認証情報: トラフィック転送方式

TLS終端プロキシで暗号化されたトラフィックを復号化・検査・変更・再暗号化。以下が必要:
1. エージェントのコンテナの外側でプロキシを実行
2. エージェントのトラストストアにプロキシのCA証明書をインストール
3. `HTTP_PROXY`/`HTTPS_PROXY`を設定

### ファイルシステム設定

#### 読み取り専用コードマウント

```
docker run -v /path/to/code:/workspace:ro agent-image
```

**除外すべき機密ファイル:**

| ファイル | リスク |
|---------|-------|
| `.env`、`.env.local` | APIキー、データベースパスワード、シークレット |
| `~/.git-credentials` | プレーンテキストのGitパスワード/トークン |
| `~/.aws/credentials` | AWSアクセスキー |
| `~/.config/gcloud/application_default_credentials.json` | Google Cloud ADCトークン |
| `~/.azure/` | Azure CLI認証情報 |
| `~/.docker/config.json` | Dockerレジストリ認証トークン |
| `~/.kube/config` | Kubernetesクラスター認証情報 |
| `.npmrc`、`.pypirc` | パッケージレジストリトークン |
| `*-service-account.json` | GCPサービスアカウントキー |
| `*.pem`、`*.key` | 秘密鍵 |

#### 書き込み可能な場所

一時的なワークスペース（コンテナ停止時にクリア）:

```
docker run \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  --tmpfs /workspace:rw,noexec,size=500m \
  agent-image
```

変更を永続化前にレビューしたい場合はオーバーレイファイルシステムを使用。完全に永続的な出力には専用ボリュームをマウント。

---

## 3. コストと使用量の追跡

### トークン使用量の主要概念

| 概念 | 説明 |
|------|------|
| ステップ | アプリケーションとClaude間の単一のリクエスト/レスポンスのペア |
| メッセージ | ステップ内の個々のメッセージ（テキスト、ツール使用、ツール結果） |
| 使用量 | アシスタントメッセージに付随するトークン消費データ |

### 使用量レポートの構造

```
import { query } from "@anthropic-ai/claude-agent-sdk";

const result = await query({
  prompt: "Analyze this codebase and run tests",
  options: {
    onMessage: (message) => {
      if (message.type === 'assistant' && message.usage) {
        console.log(`Message ID: ${message.id}`);
        console.log(`Usage:`, message.usage);
      }
    }
  }
});
```

### メッセージフローの例

```
<!-- ステップ1: 並列ツール使用を含む初期リクエスト -->
assistant (text)      { id: "msg_1", usage: { output_tokens: 100, ... } }
assistant (tool_use)  { id: "msg_1", usage: { output_tokens: 100, ... } }
assistant (tool_use)  { id: "msg_1", usage: { output_tokens: 100, ... } }
assistant (tool_use)  { id: "msg_1", usage: { output_tokens: 100, ... } }
user (tool_result)
user (tool_result)
user (tool_result)

<!-- ステップ2: フォローアップレスポンス -->
assistant (text)      { id: "msg_2", usage: { output_tokens: 98, ... } }
```

### 重要な使用量ルール

1. **同じID = 同じ使用量**: 同じ`id`フィールドを持つメッセージは同一の使用量を報告。ユニークなメッセージIDごとに1回だけ課金する

```
const messages = [
  { type: 'assistant', id: 'msg_123', usage: { output_tokens: 100 } },
  { type: 'assistant', id: 'msg_123', usage: { output_tokens: 100 } },
  { type: 'assistant', id: 'msg_123', usage: { output_tokens: 100 } }
];

const uniqueUsage = messages[0].usage;
```

2. **ステップごとに1回だけ課金**: 個々のメッセージごとではなくステップごとに課金

3. **結果メッセージには累積使用量が含まれる**:

```
const result = await query({
  prompt: "Multi-step task",
  options: { /* ... */ }
});

console.log("Total usage:", result.usage);
console.log("Total cost:", result.usage.total_cost_usd);
```

4. **モデルごとの使用量内訳**: `modelUsage`でモデルごとの正式な使用量データを取得（サブエージェントにHaiku、メインエージェントにOpus等の場合に有用）

```
type ModelUsage = {
  inputTokens: number
  outputTokens: number
  cacheReadInputTokens: number
  cacheCreationInputTokens: number
  webSearchRequests: number
  costUSD: number
  contextWindow: number
}

const result = await query({ prompt: "..." });

for (const [modelName, usage] of Object.entries(result.modelUsage)) {
  console.log(`${modelName}: $${usage.costUSD.toFixed(4)}`);
  console.log(`  Input tokens: ${usage.inputTokens}`);
  console.log(`  Output tokens: ${usage.outputTokens}`);
}
```

### コスト追跡システムの実装例

```
import { query } from "@anthropic-ai/claude-agent-sdk";

class CostTracker {
  private processedMessageIds = new Set<string>();
  private stepUsages: Array<any> = [];

  async trackConversation(prompt: string) {
    const result = await query({
      prompt,
      options: {
        onMessage: (message) => {
          this.processMessage(message);
        }
      }
    });

    return {
      result,
      stepUsages: this.stepUsages,
      totalCost: result.usage?.total_cost_usd || 0
    };
  }

  private processMessage(message: any) {
    if (message.type !== 'assistant' || !message.usage) {
      return;
    }

    if (this.processedMessageIds.has(message.id)) {
      return;
    }

    this.processedMessageIds.add(message.id);
    this.stepUsages.push({
      messageId: message.id,
      timestamp: new Date().toISOString(),
      usage: message.usage,
      costUSD: this.calculateCost(message.usage)
    });
  }

  private calculateCost(usage: any): number {
    const inputCost = usage.input_tokens * 0.00003;
    const outputCost = usage.output_tokens * 0.00015;
    const cacheReadCost = (usage.cache_read_input_tokens || 0) * 0.0000075;

    return inputCost + outputCost + cacheReadCost;
  }
}

const tracker = new CostTracker();
const { result, stepUsages, totalCost } = await tracker.trackConversation(
  "Analyze and refactor this code"
);

console.log(`Steps processed: ${stepUsages.length}`);
console.log(`Total cost: $${totalCost.toFixed(4)}`);
```

### 課金ダッシュボード構築例

```
class BillingAggregator {
  private userUsage = new Map<string, {
    totalTokens: number;
    totalCost: number;
    conversations: number;
  }>();

  async processUserRequest(userId: string, prompt: string) {
    const tracker = new CostTracker();
    const { result, stepUsages, totalCost } = await tracker.trackConversation(prompt);

    const current = this.userUsage.get(userId) || {
      totalTokens: 0,
      totalCost: 0,
      conversations: 0
    };

    const totalTokens = stepUsages.reduce((sum, step) =>
      sum + step.usage.input_tokens + step.usage.output_tokens, 0
    );

    this.userUsage.set(userId, {
      totalTokens: current.totalTokens + totalTokens,
      totalCost: current.totalCost + totalCost,
      conversations: current.conversations + 1
    });

    return result;
  }

  getUserBilling(userId: string) {
    return this.userUsage.get(userId) || {
      totalTokens: 0,
      totalCost: 0,
      conversations: 0
    };
  }
}
```

### 使用量フィールドリファレンス

| フィールド | 説明 |
|-----------|------|
| `input_tokens` | 処理されたベース入力トークン |
| `output_tokens` | レスポンスで生成されたトークン |
| `cache_creation_input_tokens` | キャッシュエントリの作成に使用されたトークン |
| `cache_read_input_tokens` | キャッシュから読み取られたトークン |
| `service_tier` | 使用されたサービスティア（例:「standard」） |
| `total_cost_usd` | USD単位の合計コスト（結果メッセージのみ） |

### キャッシュトークンの型定義

```
interface CacheUsage {
  cache_creation_input_tokens: number;
  cache_read_input_tokens: number;
  cache_creation: {
    ephemeral_5m_input_tokens: number;
    ephemeral_1h_input_tokens: number;
  };
}
```

### エッジケース

- **出力トークンの不一致**: 同じIDのメッセージで異なる`output_tokens`値が出た場合、最大値を使用。`total_cost_usd`が正式な値
- **障害時**: 会話が失敗した場合でも部分的な使用量を追跡する
- **ストリーミング**: メッセージの到着に応じて使用量を蓄積する

### コスト追跡ベストプラクティス

1. 重複排除にメッセージIDを使用する（二重課金防止）
2. 結果メッセージの正式な累積使用量を監視する
3. 監査とデバッグのためにすべての使用量データをログに記録する
4. 障害を適切に処理し部分的な使用量も追跡する
5. ストリーミングレスポンスではメッセージ到着に応じて使用量を蓄積する

---

## 設計判断ポイント

### デプロイメントパターンの選択

| 判断軸 | エフェメラル | 長時間実行 | ハイブリッド | シングルコンテナ |
|--------|-----------|-----------|------------|----------------|
| タスク特性 | 単発・完結型 | 継続的・プロアクティブ | 断続的インタラクション | エージェント間連携 |
| コスト効率 | 使用時のみ課金 | 常時稼働コスト | 中間 | 単一コンテナで効率的 |
| 状態管理 | 不要 | コンテナ内で永続 | DB/セッション再開で復元 | 共有環境で管理 |
| スケーラビリティ | タスク単位で容易 | インスタンス管理が必要 | セッション管理が必要 | 限定的 |

### 分離技術の選択

| 判断軸 | sandbox-runtime | Docker | gVisor | VM(Firecracker) |
|--------|----------------|--------|--------|-----------------|
| セットアップ容易性 | 最も簡単 | 中程度 | 中程度 | 高い |
| カーネル分離 | なし（共有） | なし（共有） | あり（ユーザースペース） | あり（ハードウェアレベル） |
| 推奨ユースケース | 単一開発者、CI/CD | 一般的な本番環境 | マルチテナント、信頼できないコンテンツ | 最高レベルの分離が必要な場合 |
| I/Oパフォーマンス | 良好 | 良好 | 劣化の可能性あり | オーバーヘッド大 |

### 認証情報管理の選択

| 判断軸 | ANTHROPIC_BASE_URL | HTTP_PROXY/HTTPS_PROXY | カスタムツール(MCP) | TLS終端プロキシ |
|--------|-------------------|----------------------|-------------------|----------------|
| 対象範囲 | Anthropic APIのみ | システム全体のHTTP | 任意のサービス | 任意のHTTPS |
| 実装複雑度 | 低い | 低い | 中程度 | 高い（証明書管理） |
| TLSインスペクション | 不要（プレーンテキスト） | 不可（CONNECTトンネル） | 不要 | 必要 |
| 認証情報の安全性 | プロキシで注入 | トンネル内で見えない | 境界外で注入 | プロキシで注入 |

### コスト最適化の判断

| 判断軸 | 推奨アプローチ |
|--------|-------------|
| 二重課金防止 | メッセージIDによる重複排除を必ず実装 |
| 正式なコスト値 | `result.usage.total_cost_usd`を使用（個別ステップの合算ではなく） |
| マルチモデル環境 | `result.modelUsage`でモデルごとのコストを分離追跡 |
| キャッシュ活用 | `cache_read_input_tokens`と`cache_creation_input_tokens`を個別追跡し、キャッシュヒット率を監視 |
| コンテナコスト vs トークンコスト | トークンが主要コスト。コンテナは最小約5セント/実行時間。エフェメラルパターンでコンテナコストを最小化 |
| maxTurns設定 | ループ防止とコスト暴走防止のために必ず設定 |
