# TypeScriptの型と境界の例

[スキル](guide.md)、type-system-discipline、boundary-disciplineの具体例。識別子と実行コードを元の形で保持する。

## 識別可能な基本型

基本型へbrandを付け、ID同士の取り違えを防ぐ。境界で一度検証し、内部では型を信頼する。既存の `readonly __brand` の形へ合わせる。

```ts
type AgentId = string & { readonly __brand: "AgentId" };

function parseAgentId(input: string): AgentId {
  if (!isUUID(input)) throw new Error(`Invalid agent id: ${input}`);
  return input as AgentId;
}

function focusAgent(id: AgentId): void {
  /* input is trusted */
}
```

## 判別できるunion

共通の判別フィールドと一意のliteral値で状態を表し、不正な組合せを作れなくする。`kind`、`type`、`tag` の一つへそろえる。

```ts
// Don't. Boolean + optionals lets contradictory states exist.
type DiffState = { loading: boolean; diff?: GitDiff; error?: string };

// Do. Only valid states exist.
type DiffState =
  | { kind: "loading" }
  | { kind: "ready"; diff: GitDiff }
  | { kind: "error"; error: string };
```

## 構成から不変条件を守る

緩い型を後で検査するより、有効な部品から型を作る。非空は可変長tuple、偶数はpair、期間は開始と長さで表せる。普通の配列を受ける境界では一度guardで絞る。期間の `number` 自体は負値を防がないため、構築時に有限・非負を検証する。brandは取り違えがある場合だけ使い、必要な読み方を導出する。

```ts
type NonEmpty<T> = [T, ...T[]];

// Don't: T[] plus a length check every caller must repeat
function pickWinner(entries: string[]): string {
  if (entries.length === 0) throw new Error("no entries");
  return entries[Math.floor(Math.random() * entries.length)];
}

// Do: an empty value of the type can't exist
function pickWinner(entries: NonEmpty<string>): string {
  return entries[Math.floor(Math.random() * entries.length)];
}
```

```ts
const isNonEmpty = <T>(arr: T[]): arr is NonEmpty<T> => arr.length > 0;
```

```ts
type Pairs<T> = [T, T][];
```

```ts
// Don't: a comment holds the invariant
type TimeRange = { start: Date; end: Date }; // start <= end

// Do: a negative range can't be written; derive end when needed
type TimeRange = { start: Date; durationMs: number };
```

## 全入力へ結果を返せる最小の型

空配列でも和が0になるなら `T[]` のままでよい。`!`、`arr[0] as T`、起こらないはずのthrowが必要なら入力を非空へ強めるか、出力を `Session | undefined` にする。

```ts
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0); // [] is 0, fine
```

```ts
// Don't: partiality smuggled past the compiler
function newestSession(sessions: Session[]): Session {
  return sessions.at(0)!;
}

// Do: strengthen the input; the assertion disappears
function newestSession(sessions: NonEmpty<Session>): Session {
  return sessions[0];
}
```

## 外部データはunknown

RPC、JSON.parse、postMessage、IPC、ファイル、環境変数、DB結果を `unknown` で受けて絞る。`any` で検査を消さない。

```ts
// Don't
function handle(input: any) {
  return input.foo.bar;
}

// Do
function handle(input: unknown) {
  if (typeof input === "object" && input !== null && "foo" in input) {
    // narrowed; compiler verifies access
  }
}
```

## 手書きguardより既存schema

repoのruntime schemaと既存の定義を探し、一つのschemaから型を導出する。schema、interface、guardを重複維持しない。失敗が通常分岐ならsafeParse等を使う。一つのguardのため新依存を入れない。

```ts
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid(),
  role: z.enum(["admin", "member"]),
});

type User = z.infer<typeof UserSchema>;

function parseUser(input: unknown): User {
  return UserSchema.parse(input);
}
```

## 根拠のないasを避ける

`as` は実行時の保証を与えない。境界で全項目を検証した場合に限定する。推論できない理由を調べ、判別子、狭い型、parse・schema、brand・satisfiesを選ぶ。以下は検査の形を示す部分例で、省略された全項目を検証せずコピーしない。

```ts
// Don't
const user = data as User;

// Do. Earn the cast at the boundary.
function parseUser(data: unknown): User {
  if (typeof data !== "object" || data === null) {
    throw new Error("expected object");
  }
  if (!("id" in data) || typeof (data as Record<string, unknown>).id !== "string") {
    throw new Error("expected id");
  }
  // ... validate all fields
  return data as User; // OK, earned cast after full validation
}
```

## 型を絞る順序

判別union、in、typeof・instanceof、利用者定義guard、検証後のasの順で選ぶ。

```ts
function area(s: Shape): number {
  if ("radius" in s) return Math.PI * s.radius ** 2; // narrowed to circle
  return s.width * s.height; // narrowed to rect
}
```

## 型guard

主張した条件を実際に検査する。嘘のguardはasより危険。可能なら判別子で絞る。

```ts
function isCircle(s: Shape): s is Shape & { kind: "circle" } {
  return s.kind === "circle";
}
```

## 全状態の網羅

defaultで `never` の変数へ代入する。値を返すswitchではreturn、処理だけのswitchではvoidを使う。

```ts
// Value-returning switch
function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * s.radius ** 2;
    case "rect":
      return s.width * s.height;
    default: {
      const _exhaustive: never = s;
      return _exhaustive;
    }
  }
}

// Void switch
function handle(s: Shape): void {
  switch (s.kind) {
    case "circle":
      drawCircle(s);
      break;
    case "rect":
      drawRect(s);
      break;
    default: {
      const _exhaustive: never = s;
      void _exhaustive;
    }
  }
}
```

## asよりsatisfies

literalの型を広げず適合を検査する。

```ts
// Don't. Widens, loses literal types.
const config = { theme: "dark", cols: 3 } as Config;

// Do. Validates AND preserves literal types.
const config = { theme: "dark", cols: 3 } satisfies Config;
// config.theme is "dark" (literal), not string
```

## 境界での検証

外部から入るところで一度検証し、内部は型を信頼する。proto等では `ignoreUnknownFields` で前方互換を保つ。保存JSONは版を付け、parseをtry/catchで扱う。深い呼び出しで再検証を重ねない。



## schemaから導く型

proto、OpenAPI、GraphQL、DB migrationが形を定めるなら生成型から導く。新しいinterfaceより先にPick、Omit、Parameters、ReturnType、Awaited、typeofを検討する。

```ts
// Don't. Duplicate shape, drifts when the schema changes.
type CheckSummary = {
  totalCount: number;
  checks: { name: string; status: string }[];
};
function renderChecks(s: CheckSummary) {
  /* ... */
}

// Do. Derive from the generated schema type.
import type { ChecksMessage } from "<generated module>";
function renderChecks(s: Pick<ChecksMessage, "totalCount" | "checks">) {
  /* ... */
}
```

## オブジェクト引数

同型引数の順序を取り違えない形を選ぶ。毎frameの描画、tokenizer、parserなど確かめた高頻度処理で割当費用が問題なら省く。

```ts
// Don't. Swap two args, still compiles.
openFile(uri, {
  startLineNumber: 10,
  startColumn: 1,
  endLineNumber: 10,
  endColumn: 1,
});

// Do. Order-independent, self-documenting.
openFile({
  uri,
  selection: {
    startLineNumber: 10,
    startColumn: 1,
    endLineNumber: 10,
    endColumn: 1,
  },
});
```
