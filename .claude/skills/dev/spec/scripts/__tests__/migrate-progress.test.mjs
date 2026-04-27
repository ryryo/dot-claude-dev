import { describe, it } from 'node:test'
import assert from 'node:assert/strict'

import { applyMigration } from '../migrate-progress.mjs'

describe('applyMigration', () => {
  it('removes progress and metadata from a v3 tasks.json', () => {
    const input = {
      schemaVersion: 3,
      spec: { slug: 'foo' },
      status: 'in-progress',
      progress: { gatesPassed: 0, gatesTotal: 1, currentGate: 'A', currentGateAC: { passed: 0, total: 2 } },
      gates: [],
      metadata: { createdAt: '2026-04-27T00:00:00Z', totalGates: 1, totalTodos: 2 },
    }

    const { changed, result, removed, skipped } = applyMigration(input)

    assert.equal(skipped, null)
    assert.equal(changed, true)
    assert.deepEqual(removed.sort(), ['metadata', 'progress'])
    assert.equal(result.progress, undefined)
    assert.equal(result.metadata, undefined)
    assert.equal(result.schemaVersion, 3)
    assert.deepEqual(result.spec, { slug: 'foo' })
    assert.equal(result.status, 'in-progress')
    assert.deepEqual(result.gates, [])
    // 入力は不変であること（純粋関数）
    assert.ok('progress' in input)
    assert.ok('metadata' in input)
  })

  it('skips non-v3 tasks.json (schemaVersion 2)', () => {
    const input = {
      schemaVersion: 2,
      progress: { gatesPassed: 0 },
      metadata: { totalGates: 0 },
    }

    const { changed, result, removed, skipped } = applyMigration(input)

    assert.equal(skipped, 'schemaVersion=2')
    assert.equal(changed, false)
    assert.deepEqual(removed, [])
    // v2 は手を加えない（同一参照）
    assert.equal(result, input)
  })

  it('is idempotent on a v3 tasks.json without progress/metadata', () => {
    const input = {
      schemaVersion: 3,
      spec: { slug: 'foo' },
      status: 'in-progress',
      gates: [],
    }

    const { changed, result, removed, skipped } = applyMigration(input)

    assert.equal(skipped, null)
    assert.equal(changed, false)
    assert.deepEqual(removed, [])
    assert.deepEqual(result, input)
  })
})
