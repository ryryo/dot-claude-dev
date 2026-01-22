#!/usr/bin/env node
/**
 * fetch-tweet.mjs
 * Puppeteerを使用してTwitter/Xのツイート内容を取得
 *
 * Usage:
 *   node scripts/fetch-tweet.mjs <tweet-url>
 *   node scripts/fetch-tweet.mjs https://x.com/i/status/2014040193557471352
 *
 * Environment:
 *   CHROME_PATH - Chromeの実行パスを指定（任意）
 */

import puppeteer from 'puppeteer-core';
import { execSync } from 'child_process';
import { existsSync } from 'fs';

const DEFAULT_TIMEOUT = 30000;

/**
 * OSに応じたChromeパスを検出
 */
function findChromePath() {
  // 環境変数で指定されている場合
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) {
    return process.env.CHROME_PATH;
  }

  const platform = process.platform;

  const paths = {
    darwin: [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
      '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
    ],
    win32: [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe',
    ],
    linux: [
      '/usr/bin/google-chrome',
      '/usr/bin/chromium-browser',
      '/usr/bin/chromium',
      '/snap/bin/chromium',
    ],
  };

  const candidates = paths[platform] || paths.linux;

  for (const path of candidates) {
    if (path && existsSync(path)) {
      return path;
    }
  }

  // whichコマンドで探す (Linux/Mac)
  if (platform !== 'win32') {
    try {
      const result = execSync('which google-chrome chromium-browser chromium 2>/dev/null', {
        encoding: 'utf8',
      }).trim().split('\n')[0];
      if (result && existsSync(result)) {
        return result;
      }
    } catch {
      // ignore
    }
  }

  return null;
}

async function fetchTweet(url) {
  const chromePath = findChromePath();

  if (!chromePath) {
    throw new Error(
      'Chrome/Chromiumが見つかりません。\n' +
      'CHROME_PATH環境変数でパスを指定するか、Chromeをインストールしてください。\n' +
      '例: CHROME_PATH="/path/to/chrome" node scripts/fetch-tweet.mjs <url>'
    );
  }

  console.error(`Using browser: ${chromePath}`);
  console.error(`Fetching: ${url}`);

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  try {
    const page = await browser.newPage();

    // User-Agentを設定
    await page.setUserAgent(
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    // ビューポート設定
    await page.setViewport({ width: 1280, height: 900 });

    // ページ遷移
    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: DEFAULT_TIMEOUT
    });

    // ツイート本文がレンダリングされるまで待機
    await page.waitForSelector('article[data-testid="tweet"]', {
      timeout: DEFAULT_TIMEOUT
    });

    // 動的コンテンツのレンダリング完了待ち
    await new Promise(resolve => setTimeout(resolve, 2000));

    // ツイート情報を抽出
    const tweetData = await page.evaluate(() => {
      const article = document.querySelector('article[data-testid="tweet"]');
      if (!article) return null;

      // ユーザー名
      const userNameEl = article.querySelector('[data-testid="User-Name"]');
      const userName = userNameEl?.textContent || '';

      // ツイート本文
      const tweetTextEl = article.querySelector('[data-testid="tweetText"]');
      const tweetText = tweetTextEl?.textContent || '';

      // 日時
      const timeEl = article.querySelector('time');
      const timestamp = timeEl?.getAttribute('datetime') || '';
      const displayTime = timeEl?.textContent || '';

      // 画像URLs
      const images = Array.from(article.querySelectorAll('img[src*="pbs.twimg.com/media"]'))
        .map(img => img.src);

      // リンク
      const links = Array.from(article.querySelectorAll('a[href]'))
        .map(a => a.href)
        .filter(href => href && !href.includes('twitter.com') && !href.includes('x.com'));

      return {
        userName,
        tweetText,
        timestamp,
        displayTime,
        images,
        links
      };
    });

    // スレッド全体を取得
    const threadData = await page.evaluate(() => {
      const articles = document.querySelectorAll('article[data-testid="tweet"]');
      return Array.from(articles).map((article, index) => {
        const userNameEl = article.querySelector('[data-testid="User-Name"]');
        const tweetTextEl = article.querySelector('[data-testid="tweetText"]');
        const timeEl = article.querySelector('time');

        return {
          index: index + 1,
          userName: userNameEl?.textContent || '',
          text: tweetTextEl?.textContent || '',
          timestamp: timeEl?.getAttribute('datetime') || ''
        };
      });
    });

    return {
      url,
      fetchedAt: new Date().toISOString(),
      mainTweet: tweetData,
      thread: threadData
    };

  } finally {
    await browser.close();
  }
}

// Markdown形式で出力
function toMarkdown(data) {
  const lines = [];
  lines.push(`# Tweet: ${data.url}`);
  lines.push(`Fetched: ${data.fetchedAt}`);
  lines.push('');

  if (data.mainTweet) {
    lines.push(`## Main Tweet`);
    lines.push(`**User**: ${data.mainTweet.userName}`);
    lines.push(`**Time**: ${data.mainTweet.displayTime}`);
    lines.push('');
    lines.push(data.mainTweet.tweetText);
    lines.push('');

    if (data.mainTweet.images.length > 0) {
      lines.push('### Images');
      data.mainTweet.images.forEach(img => lines.push(`- ${img}`));
      lines.push('');
    }
  }

  if (data.thread && data.thread.length > 1) {
    lines.push('## Thread');
    data.thread.forEach(tweet => {
      lines.push(`### ${tweet.index}. ${tweet.userName}`);
      lines.push(tweet.text);
      lines.push('');
    });
  }

  return lines.join('\n');
}

// メイン実行
const args = process.argv.slice(2);
const url = args.find(arg => arg.startsWith('http'));
const outputMarkdown = args.includes('--markdown') || args.includes('-m');

if (!url) {
  console.error('Usage: node scripts/fetch-tweet.mjs <tweet-url> [--markdown]');
  console.error('');
  console.error('Options:');
  console.error('  --markdown, -m  Output as Markdown instead of JSON');
  console.error('');
  console.error('Environment:');
  console.error('  CHROME_PATH     Path to Chrome/Chromium executable');
  process.exit(1);
}

if (!url.includes('x.com') && !url.includes('twitter.com')) {
  console.error('Error: URL must be a Twitter/X URL');
  process.exit(1);
}

try {
  const result = await fetchTweet(url);

  if (outputMarkdown) {
    console.log(toMarkdown(result));
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}
