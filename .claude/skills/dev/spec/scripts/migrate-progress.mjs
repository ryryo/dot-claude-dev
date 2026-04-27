#!/usr/bin/env node
/**
 * tasks.json schemaVersion 3 から `progress` / `metadata` キーを削除する idempotent migration script.
 *
 * Usage:
 *   node migrate-progress.mjs [--dry-run] [<glob>]
 *
 * - `<glob>` 省略時は `docs/PLAN/<asterisk>/tasks.json` をデフォルト対象
 * - `--dry-run` を渡すと書き込みせず変更予定のみ stdout に出力
 * - 実行モードでは progress/metadata を削除した後 sync-spec-md.mjs を子プロセス呼び出しして spec.md を再同期
 *
 * Public API (vitest 用):
 *   applyMigration(parsedJson) -> { changed: boolean, result: object, removed: string[], skipped: string | null }
 */

import { readFile, writeFile, readdir, stat } from 'node:fs/promises'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { resolve, join } from 'node:path'

const REMOVABLE_KEYS = ['progress', 'metadata']
const DEFAULT_GLOB = 'docs/PLAN/*/tasks.json'
const SYNC_SPEC_MD_PATH = '.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs'

/**
 * In-memory migration. Pure function. (vitest 用)
 *
 * @param {object} parsed - JSON.parse 済みのオブジェクト
 * @returns {{ changed: boolean, result: object, removed: string[], skipped: string | null }}
 *   - skipped !== null: スキップ理由（schemaVersion 不一致など）
 *   - removed: 削除されたキー名（空配列なら冪等）
 */
export function applyMigration(parsed) {
  if (!parsed || typeof parsed !== 'object') {
    return { changed: false, result: parsed, removed: [], skipped: 'not-an-object' }
  }
  if (parsed.schemaVersion !== 3) {
    return {
      changed: false,
      result: parsed,
      removed: [],
      skipped: `schemaVersion=${JSON.stringify(parsed.schemaVersion)}`,
    }
  }

  const removed = []
  const result = { ...parsed }
  for (const key of REMOVABLE_KEYS) {
    if (key in result) {
      delete result[key]
      removed.push(key)
    }
  }

  return { changed: removed.length > 0, result, removed, skipped: null }
}

/**
 * Minimal glob: `<basedir>/<segment-glob>/<filename>` のパターン専用.
 * 例: `docs/PLAN/*<asterisk>/tasks.json` → docs/PLAN 配下の各サブディレクトリ内の tasks.json を返す.
 * Node 20 環境では `node:fs/promises` の glob が使えないので自前実装で十分なケースに限定する.
 */
async function expandGlob(pattern, cwd) {
  // pattern を <baseDir>/<wildcard>/<basename> に分解
  const parts = pattern.split('/')
  const wildcardIdx = parts.findIndex((p) => p.includes('*'))
  if (wildcardIdx === -1) {
    // wildcard 無し → そのまま返す
    const abs = resolve(cwd, pattern)
    try {
      await stat(abs)
      return [abs]
    } catch {
      return []
    }
  }
  const baseParts = parts.slice(0, wildcardIdx)
  const wildcardSegment = parts[wildcardIdx]
  const tailParts = parts.slice(wildcardIdx + 1)
  if (wildcardSegment !== '*') {
    throw new Error(
      `expandGlob: only single-segment '*' wildcards are supported (got: ${wildcardSegment})`,
    )
  }
  const baseDir = resolve(cwd, ...baseParts)
  let entries
  try {
    entries = await readdir(baseDir)
  } catch {
    return []
  }
  const matches = []
  for (const entry of entries) {
    const candidate = join(baseDir, entry, ...tailParts)
    try {
      const s = await stat(candidate)
      if (s.isFile()) matches.push(candidate)
    } catch {
      // skip non-existent
    }
  }
  return matches.sort()
}

async function processFile(filePath, { dryRun }) {
  const raw = await readFile(filePath, 'utf8')
  let parsed
  try {
    parsed = JSON.parse(raw)
  } catch (err) {
    return { filePath, status: 'error', error: `JSON parse error: ${err.message}` }
  }

  const { changed, result, removed, skipped } = applyMigration(parsed)

  if (skipped) {
    return { filePath, status: 'skipped', reason: skipped }
  }
  if (!changed) {
    return { filePath, status: 'noop' }
  }
  if (dryRun) {
    return { filePath, status: 'dry-run', removed }
  }

  const serialized = JSON.stringify(result, null, 2) + '\n'
  await writeFile(filePath, serialized, 'utf8')

  // sync-spec-md.mjs 子プロセス呼び出し
  const projectRoot = process.cwd()
  const syncScript = resolve(projectRoot, SYNC_SPEC_MD_PATH)
  const sync = spawnSync('node', [syncScript, filePath], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  return {
    filePath,
    status: 'updated',
    removed,
    syncStatus: sync.status,
    syncStdout: sync.stdout?.trim() ?? '',
    syncStderr: sync.stderr?.trim() ?? '',
  }
}

async function main(argv) {
  const args = argv.slice(2)
  const dryRun = args.includes('--dry-run')
  const positional = args.filter((a) => !a.startsWith('--'))
  const pattern = positional[0] ?? DEFAULT_GLOB

  const cwd = process.cwd()
  const targets = await expandGlob(pattern, cwd)

  if (targets.length === 0) {
    console.log(`[migrate-progress] no files matched: ${pattern}`)
    return 0
  }

  console.log(`[migrate-progress] mode=${dryRun ? 'dry-run' : 'apply'} pattern=${pattern} matches=${targets.length}`)

  let updated = 0
  let skipped = 0
  let noop = 0
  let errors = 0

  for (const file of targets) {
    const result = await processFile(file, { dryRun })
    const rel = file.replace(cwd + '/', '')
    switch (result.status) {
      case 'updated':
        console.log(`  [updated] ${rel} removed=${result.removed.join(',')} sync=${result.syncStatus}`)
        if (result.syncStderr) console.log(`            sync stderr: ${result.syncStderr}`)
        updated++
        break
      case 'dry-run':
        console.log(`  [dry-run] ${rel} would-remove=${result.removed.join(',')}`)
        updated++
        break
      case 'noop':
        console.log(`  [noop] ${rel} (already migrated)`)
        noop++
        break
      case 'skipped':
        console.log(`  [skip] ${rel} reason=${result.reason}`)
        skipped++
        break
      case 'error':
        console.error(`  [error] ${rel}: ${result.error}`)
        errors++
        break
    }
  }

  console.log(`[migrate-progress] summary: updated=${updated} noop=${noop} skipped=${skipped} errors=${errors}`)
  return errors > 0 ? 1 : 0
}

// CLI entry only when invoked directly
const isDirect =
  import.meta.url === `file://${process.argv[1]}` ||
  import.meta.url === fileURLToPath(import.meta.url)
if (isDirect) {
  main(process.argv).then(
    (code) => process.exit(code),
    (err) => {
      console.error(err)
      process.exit(1)
    },
  )
}
