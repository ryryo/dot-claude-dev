/**
 * browser.js - Puppeteer ブラウザ起動・管理
 */

import puppeteer from 'puppeteer';

/**
 * 指定時間待機するヘルパー関数
 * @param {number} ms 待機時間（ミリ秒）
 */
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Puppeteer ブラウザインスタンスを起動
 * @returns {Promise<import('puppeteer').Browser>}
 */
export async function getBrowser() {
  console.log('[Browser] Launching headless Chrome...');

  return puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--lang=ja-JP,ja',
      '--font-render-hinting=none',
      '--disable-gpu',
      '--disable-gpu-compositing',
      '--disable-accelerated-video-decode',
      '--disable-accelerated-2d-canvas',
      '--use-gl=swiftshader',
      '--use-angle=swiftshader',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-background-media-suspend',
      '--disable-features=IsolateOrigins,site-per-process',
      '--disable-web-security',
    ],
  });
}

/**
 * ページを設定して指定URLに移動
 * @param {import('puppeteer').Browser} browser
 * @param {string} url
 * @param {object} options
 * @param {number} [options.width=1024]
 * @param {number} [options.height=3840]
 * @param {number} [options.timeout=60000]
 * @returns {Promise<import('puppeteer').Page>}
 */
export async function setupPage(browser, url, options = {}) {
  const { width = 1024, height = 3840, timeout = 60000 } = options;

  const page = await browser.newPage();

  console.log(`[Browser] Setting viewport to ${width}x${height}...`);
  await page.setViewport({ width, height });

  await page.setExtraHTTPHeaders({
    'Accept-Language': 'ja-JP,ja;q=0.9',
  });

  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  );

  console.log(`[Browser] Navigating to: ${url}`);
  const networkIdleTimeout = 30000;

  try {
    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: networkIdleTimeout,
    });
    console.log('[Browser] Page navigation complete (networkidle2).');
  } catch (error) {
    if (error.name === 'TimeoutError') {
      console.warn(
        `[Browser] networkidle2 timeout (${networkIdleTimeout}ms), falling back to 'load' event...`
      );
      await page.goto(url, {
        waitUntil: 'load',
        timeout: timeout - networkIdleTimeout,
      });
      console.log('[Browser] Page navigation complete (using load event).');
      await delay(2000);
    } else {
      throw error;
    }
  }

  return page;
}
