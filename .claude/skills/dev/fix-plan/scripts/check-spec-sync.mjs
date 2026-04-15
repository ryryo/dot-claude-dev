#!/usr/bin/env node
// @ts-check
/**
 * tasks.json と spec.md の generated 領域の同期状態をチェックする。
 * sync-spec-md.mjs の generateTaskListSection を呼び出して差分を検出。
 *
 * Usage:
 *   node check-spec-sync.mjs <path-to-tasks.json>
 *
 * 出力: JSON { synced, generatedRegion, currentRegion, diff }
 */
import { readFileSync, existsSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const BEGIN_MARKER = '<!-- generated:begin -->';
const END_MARKER = '<!-- generated:end -->';

function extractGeneratedRegion(specContent) {
  const beginIdx = specContent.indexOf(BEGIN_MARKER);
  const endIdx = specContent.indexOf(END_MARKER);
  if (beginIdx < 0 || endIdx < 0 || endIdx < beginIdx) {
    return null;
  }
  // Return the content between markers (exclusive of markers themselves)
  return specContent.slice(beginIdx + BEGIN_MARKER.length, endIdx).trim();
}

async function main() {
  const tasksPath = process.argv[2];
  if (!tasksPath) {
    console.error('Usage: check-spec-sync.mjs <path-to-tasks.json>');
    process.exit(1);
  }

  const absPath = resolve(tasksPath);
  if (!existsSync(absPath)) {
    console.error(`File not found: ${absPath}`);
    process.exit(1);
  }

  let tj;
  try {
    tj = JSON.parse(readFileSync(absPath, 'utf-8'));
  } catch (err) {
    console.error(`JSON parse error: ${err.message}`);
    process.exit(1);
  }

  if (typeof tj.schemaVersion !== 'number' || tj.schemaVersion < 2) {
    console.error('Not a v2 tasks.json, skipping spec sync check.');
    process.exit(0);
  }

  const specPath = resolve(dirname(absPath), tj.spec?.specPath || 'spec.md');
  if (!existsSync(specPath)) {
    const result = { synced: false, markersFound: false, error: `spec.md not found at ${specPath}` };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
  }

  const specContent = readFileSync(specPath, 'utf-8');
  const currentRegion = extractGeneratedRegion(specContent);

  if (currentRegion === null) {
    const result = { synced: false, markersFound: false, error: 'generated markers not found in spec.md' };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
  }

  // Import generateTaskListSection from sync-spec-md.mjs
  const syncScriptPath = resolve(
    dirname(absPath),
    '../../../../.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs'
  );
  // Try multiple resolution strategies
  const candidates = [
    syncScriptPath,
    resolve(process.cwd(), '.claude/skills/dev/spec-run/scripts/sync-spec-md.mjs'),
  ];

  let generateTaskListSection;
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      const mod = await import(pathToFileURL(candidate).href);
      generateTaskListSection = mod.generateTaskListSection;
      break;
    }
  }

  if (!generateTaskListSection) {
    // Fallback: inline minimal version for basic check
    const result = {
      synced: null,
      markersFound: true,
      error: 'sync-spec-md.mjs not found, cannot generate expected region',
      currentRegionLength: currentRegion.length,
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  }

  const expectedRegion = generateTaskListSection(tj).trim();
  const synced = currentRegion === expectedRegion;

  const result = {
    synced,
    markersFound: true,
    currentLength: currentRegion.length,
    expectedLength: expectedRegion.length,
  };

  if (!synced) {
    // Show first difference
    const lines_current = currentRegion.split('\n');
    const lines_expected = expectedRegion.split('\n');
    const firstDiff = lines_current.findIndex((line, i) => line !== lines_expected[i]);
    result.firstDiffLine = firstDiff >= 0 ? firstDiff + 1 : null;
    if (firstDiff >= 0) {
      result.currentAtDiff = lines_current[firstDiff] || '(eof)';
      result.expectedAtDiff = lines_expected[firstDiff] || '(eof)';
    }
  }

  console.log(JSON.stringify(result, null, 2));
  process.exit(synced ? 0 : 1);
}

const isDirectRun = import.meta.main ?? (
  process.argv[1] &&
  import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
);
if (isDirectRun) main();
