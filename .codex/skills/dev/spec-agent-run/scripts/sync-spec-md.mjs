#!/usr/bin/env node
// @ts-check
import { readFileSync, writeFileSync, existsSync, realpathSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const BEGIN_MARKER = '<!-- generated:begin -->'
const END_MARKER = '<!-- generated:end -->'

/**
 * Generate the spec.md generated section from a schema v3 tasks.json object.
 * @param {any} tasksJson
 * @returns {string}
 */
export function generateTaskListSection(tasksJson) {
  const lines = []
  lines.push('<!-- このセクションは sync-spec-md が tasks.json から自動生成します。-->')
  lines.push('<!-- 手動編集は反映されません。変更は tasks.json に対して行ってください。-->')
  lines.push('')
  lines.push('### 依存関係図')
  lines.push('')
  lines.push('```')
  for (const gate of tasksJson.gates ?? []) {
    const deps = (gate.dependencies ?? []).join(', ')
    const suffix = deps ? `（Gate ${deps} 完了後）` : ''
    lines.push(`Gate ${gate.id}: ${gate.title}${suffix}`)
  }
  lines.push('```')
  lines.push('')

  for (const gate of tasksJson.gates ?? []) {
    lines.push(`### Gate ${gate.id}: ${gate.title}`)
    lines.push('')
    if (gate.summary && gate.summary.trim() !== '') {
      lines.push(`> ${gate.summary}`)
      lines.push('')
    }

    const what = gate.goal?.what ?? ''
    const why = gate.goal?.why ?? ''
    if (what || why) {
      const whySuffix = why ? ` — ${why}` : ''
      lines.push(`**Goal**: ${what}${whySuffix}`)
      lines.push('')
    }

    const must = gate.constraints?.must ?? []
    const mustNot = gate.constraints?.mustNot ?? []
    if (must.length > 0 || mustNot.length > 0) {
      lines.push('**Constraints**:')
      for (const item of must) {
        lines.push(`- ✅ MUST: ${item}`)
      }
      for (const item of mustNot) {
        lines.push(`- ❌ MUST NOT: ${item}`)
      }
      lines.push('')
    }

    const ac = gate.acceptanceCriteria ?? []
    if (ac.length > 0) {
      lines.push('**Acceptance Criteria**:')
      for (const item of ac) {
        const box = item.checked ? 'x' : ' '
        lines.push(`- [${box}] **${item.id}**: ${item.description}`)
      }
      lines.push('')
    }

    const todos = gate.todos ?? []
    if (todos.length > 0) {
      lines.push(`**Todos** (${todos.length}):`)
      for (const todo of todos) {
        const files = (todo.affectedFiles ?? []).map((f) => `\`${f.path}\``)
        let filesSuffix = ''
        if (files.length === 1) {
          filesSuffix = ` — ${files[0]}`
        } else if (files.length === 2) {
          filesSuffix = ` — ${files.join(', ')}`
        } else if (files.length > 2) {
          filesSuffix = ` — ${files.slice(0, 2).join(', ')} ほか`
        }
        lines.push(`- **${todo.id}**: ${todo.title}${filesSuffix}`)
      }
      lines.push('')
    }

    lines.push(`**Review**: ${formatReviewLine(gate.review ?? null)}`)
    lines.push('')
  }

  while (lines.length > 0 && lines[lines.length - 1] === '') {
    lines.pop()
  }
  lines.push('')

  return lines.join('\n')
}

/**
 * @param {any} review
 * @returns {string}
 */
function formatReviewLine(review) {
  if (!review) {
    return '_未記入_'
  }
  const { result, fixCount, summary } = review
  const fixStr = fixCount > 0 ? ` (FIX ${fixCount}回)` : ''
  const summaryStr = summary ? ` — ${summary}` : ''
  switch (result) {
    case 'PASSED': return `✅ PASSED${fixStr}${summaryStr}`
    case 'FAILED': return `❌ FAILED${summaryStr}`
    case 'SKIPPED': return `⏭️ SKIPPED${summaryStr}`
    case 'IN_PROGRESS': return `⏳ IN_PROGRESS${summaryStr}`
    default: return `${result}${summaryStr}`
  }
}

/**
 * Replace the generated section inside spec.md.
 * @param {string} specContent
 * @param {string} generatedSection
 * @returns {{ content: string, replaced: boolean }}
 */
export function replaceGeneratedSection(specContent, generatedSection) {
  const beginIdx = specContent.indexOf(BEGIN_MARKER)
  const endIdx = specContent.indexOf(END_MARKER)
  if (beginIdx < 0 || endIdx < 0 || endIdx < beginIdx) {
    return { content: specContent, replaced: false }
  }
  const before = specContent.slice(0, beginIdx + BEGIN_MARKER.length)
  const after = specContent.slice(endIdx)
  const next = `${before}\n${generatedSection}\n${after}`
  return { content: next, replaced: true }
}

function main() {
  const tasksJsonPath = process.argv[2]
  if (!tasksJsonPath) {
    console.error('Usage: sync-spec-md.mjs <tasks-json-path>')
    process.exit(1)
  }

  const absPath = resolve(tasksJsonPath)
  if (!existsSync(absPath)) {
    console.error(`sync-spec-md: tasks.json not found at ${absPath}`)
    process.exit(0)
  }

  let tasksJson
  try {
    tasksJson = JSON.parse(readFileSync(absPath, 'utf-8'))
  } catch (err) {
    console.error(`sync-spec-md: failed to parse tasks.json: ${err.message}`)
    process.exit(0)
  }

  if (typeof tasksJson?.schemaVersion !== 'number' || tasksJson.schemaVersion < 3) {
    process.exit(0)
  }

  const specPath = resolve(dirname(absPath), 'spec.md')
  if (!existsSync(specPath)) {
    console.error(`sync-spec-md: spec.md not found at ${specPath}, skipping`)
    process.exit(0)
  }

  const specContent = readFileSync(specPath, 'utf-8')
  const generatedSection = generateTaskListSection(tasksJson)
  const { content: newContent, replaced } = replaceGeneratedSection(specContent, generatedSection)

  if (!replaced) {
    console.error(`sync-spec-md: generated markers not found in ${specPath}, skipping`)
    process.exit(0)
  }

  if (newContent !== specContent) {
    writeFileSync(specPath, newContent, 'utf-8')
    console.error(`sync-spec-md: updated ${specPath}`)
  }
}

const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
)
if (isDirectRun) {
  main()
}
