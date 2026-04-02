#!/usr/bin/env node

import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { autoScroll } from './lib/autoScroll.js';
import { getBrowser, setupPage } from './lib/browser.js';
import { takeFullPageScreenshot } from './lib/largeScreenshot.js';
import { splitByDom } from './lib/splitSections.js';
import { waitForAllMedia } from './lib/waitForMedia.js';

function parseArgs(args) {
  const options = {
    url: '',
    output: '.tmp/design-e2e-qa/screenshots/screenshot.jpg',
    width: 1440,
    height: 2560,
    timeout: 60,
    scrollStep: null,
    scrollDelay: 500,
    maxScrolls: 30,
    noScroll: false,
    splitSections: false,
    help: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--help':
      case '-h':
        options.help = true;
        break;
      case '--output':
      case '-o':
        options.output = args[++i];
        break;
      case '--width':
      case '-w': {
        const widthValue = args[++i];
        const width = parseInt(widthValue, 10);
        if (Number.isNaN(width) || width <= 0) {
          console.error(`Error: Invalid width value: ${widthValue}`);
          process.exit(1);
        }
        options.width = width;
        break;
      }
      case '--height': {
        const heightValue = args[++i];
        const height = parseInt(heightValue, 10);
        if (Number.isNaN(height) || height <= 0) {
          console.error(`Error: Invalid height value: ${heightValue}`);
          process.exit(1);
        }
        options.height = height;
        break;
      }
      case '--timeout':
        options.timeout = parseInt(args[++i], 10);
        break;
      case '--scroll-step':
        options.scrollStep = parseInt(args[++i], 10);
        break;
      case '--scroll-delay':
        options.scrollDelay = parseInt(args[++i], 10);
        break;
      case '--max-scrolls':
        options.maxScrolls = parseInt(args[++i], 10);
        break;
      case '--no-scroll':
        options.noScroll = true;
        break;
      case '--split-sections':
        options.splitSections = true;
        break;
      default:
        if (arg.startsWith('http://') || arg.startsWith('https://')) {
          options.url = arg;
        }
    }
  }

  return options;
}

function showHelp() {
  console.log(`
Usage: node screenshot.js <url> [options]

Take a full page screenshot with lazy-loaded content support.
Output is JPEG compressed (quality: 85) for smaller file sizes.

Arguments:
  <url>                     URL to screenshot (required)

Options:
  --output, -o <path>       Output file path (default: .tmp/design-e2e-qa/screenshots/screenshot.jpg)
  --width, -w <number>      Viewport width in pixels (default: 1440)
  --height <number>         Viewport height in pixels (default: 2560)
  --timeout <number>        Navigation timeout in seconds (default: 60)
  --scroll-step <number>    Scroll step in pixels (default: viewport height)
  --scroll-delay <number>   Delay between scrolls in ms (default: 500)
  --max-scrolls <number>    Maximum scroll iterations (default: 30)
  --no-scroll               Disable auto-scroll (skip lazy-load handling)
  --split-sections          Also save section-level crops based on DOM layout
  --help, -h                Show this help message

Examples:
  node screenshot.js http://localhost:4321/
  node screenshot.js http://localhost:4321/ -o .tmp/design-e2e-qa/screenshots/top-desktop-full.jpg
  node screenshot.js http://localhost:4321/ --width 768 --height 1024 --split-sections
  `);
}

async function main() {
  const args = process.argv.slice(2);
  const options = parseArgs(args);

  if (options.help) {
    showHelp();
    process.exit(0);
  }

  if (!options.url) {
    console.error('Error: URL is required.');
    showHelp();
    process.exit(1);
  }

  let browser = null;

  try {
    const startTime = Date.now();
    console.log(`\n[Main] Starting screenshot capture for: ${options.url}\n`);

    browser = await getBrowser();

    const page = await setupPage(browser, options.url, {
      width: options.width,
      height: options.height,
      timeout: options.timeout * 1000,
    });

    page.on('console', (msg) => {
      const type = msg.type();
      if (type === 'log' || type === 'warning' || type === 'error') {
        console.log(`[Browser Console] ${msg.text()}`);
      }
    });

    if (!options.noScroll) {
      console.log('\n[Main] Performing auto-scroll for lazy-loaded content...\n');
      await autoScroll(page, {
        step: options.scrollStep ?? options.height,
        delay: options.scrollDelay,
        maxScrolls: options.maxScrolls,
      });
    } else {
      console.log('\n[Main] Auto-scroll disabled. Skipping...\n');
    }

    console.log('\n[Main] Waiting for media elements to load...\n');
    await waitForAllMedia(page);

    console.log('\n[Main] Final wait before screenshot capture...\n');
    await new Promise((resolve) => setTimeout(resolve, 1000));

    console.log('\n[Main] Taking full page screenshot...\n');
    const screenshot = await takeFullPageScreenshot(page);

    const outputPath = resolve(options.output);
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, screenshot);
    console.log(`\n[Main] Screenshot saved to: ${outputPath}`);

    if (options.splitSections) {
      console.log('\n[Main] Splitting screenshot by DOM sections...\n');
      const sections = await splitByDom(page, screenshot, outputPath);
      console.log(`[Main] Saved ${sections.length} section screenshot(s).`);
      sections.forEach((section) => {
        console.log(
          `[Main] Section: ${section.fileName} (${section.left},${section.top} ${section.width}x${section.height})`
        );
      });
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[Main] Completed in ${duration}s\n`);
    process.exit(0);
  } catch (error) {
    console.error('\n[Main] Error:', error.message);
    if (error.stack) {
      console.error('[Main] Stack:', error.stack);
    }
    process.exit(1);
  } finally {
    if (browser) {
      console.log('[Main] Closing browser...');
      await browser.close();
    }
  }
}

main();
