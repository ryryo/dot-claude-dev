/**
 * largeScreenshot.js - 大画像分割キャプチャ
 *
 * Chromium のソフトウェアGLバックエンドの最大テクスチャサイズ制限（16384px）
 * を超えるページに対応するため、分割キャプチャして結合する
 */

import sharp from 'sharp';

const MAX_SIZE_PX = 16384;
const JPEG_QUALITY = 85;

/**
 * フルページスクリーンショットを取得
 * ページサイズが制限を超える場合は分割キャプチャして結合
 *
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 * @returns {Promise<Buffer>} - JPEG画像バッファ
 */
export async function takeFullPageScreenshot(page) {
  const pageHeight = await getPageHeight(page);
  const viewport = page.viewport();

  if (!viewport) {
    throw new Error('Viewport is not set.');
  }

  const deviceScaleFactor = viewport.deviceScaleFactor ?? 1;
  const width = viewport.width;
  const scaledHeight = pageHeight * deviceScaleFactor;
  const scaledWidth = width * deviceScaleFactor;

  console.log(
    `[Screenshot] Page dimensions: ${scaledWidth}x${scaledHeight}px (scaled)`
  );

  if (scaledHeight > MAX_SIZE_PX || scaledWidth > MAX_SIZE_PX) {
    console.log(
      `[Screenshot] Page exceeds MAX_SIZE_PX (${MAX_SIZE_PX}px). Using chunked capture...`
    );
    return captureLargeScreenshot(page, pageHeight, width, deviceScaleFactor);
  }

  console.log('[Screenshot] Taking direct full page screenshot...');
  const screenshot = await page.screenshot({
    fullPage: true,
    type: 'png',
    encoding: 'binary',
  });

  if (!(screenshot instanceof Buffer)) {
    throw new Error('Screenshot did not return a Buffer.');
  }

  const converted = await sharp(screenshot)
    .jpeg({ quality: JPEG_QUALITY, mozjpeg: true })
    .toBuffer();

  console.log(`[Screenshot] Size: ${(converted.length / 1024 / 1024).toFixed(2)}MB`);
  return converted;
}

async function captureLargeScreenshot(
  page,
  pageHeight,
  width,
  deviceScaleFactor
) {
  const screenshots = [];
  let currentYPosition = 0;

  const scaledPageHeight = pageHeight * deviceScaleFactor;
  const scaledWidth = width * deviceScaleFactor;
  const maxChunkHeightUnscaled = Math.floor(MAX_SIZE_PX / deviceScaleFactor);

  console.log(
    `[Screenshot] Chunked capture: total height ${pageHeight}px (scaled: ${scaledPageHeight}px)`
  );

  while (currentYPosition < pageHeight) {
    const remainingHeight = pageHeight - currentYPosition;
    const clipHeight = Math.min(maxChunkHeightUnscaled, remainingHeight);

    console.log(
      `[Screenshot] Capturing chunk at Y=${currentYPosition}px, height=${clipHeight}px`
    );

    const screenshot = await page.screenshot({
      clip: {
        x: 0,
        y: currentYPosition,
        width,
        height: clipHeight,
      },
      type: 'png',
      encoding: 'binary',
    });

    if (screenshot instanceof Buffer) {
      screenshots.push(screenshot);
    }

    currentYPosition += clipHeight;
  }

  console.log(`[Screenshot] Captured ${screenshots.length} chunks. Stitching...`);

  return stitchImages(scaledWidth, scaledPageHeight, screenshots);
}

async function stitchImages(width, height, screenshots) {
  const compositeOperations = [];
  let currentHeight = 0;

  for (let i = 0; i < screenshots.length; i++) {
    const screenshotBuffer = screenshots[i];

    try {
      const img = sharp(screenshotBuffer);
      const metadata = await img.metadata();
      const imgHeight = metadata.height;

      if (!imgHeight) {
        console.warn(
          `[Screenshot] Could not get height for chunk ${i}. Skipping.`
        );
        continue;
      }

      compositeOperations.push({
        input: screenshotBuffer,
        top: currentHeight,
        left: 0,
      });

      currentHeight += imgHeight;
    } catch (err) {
      console.error(`[Screenshot] Error processing chunk ${i}:`, err);
      throw err;
    }
  }

  console.log(`[Screenshot] Creating final canvas ${width}x${height}px...`);

  const finalImage = sharp({
    create: {
      width: Math.max(1, width),
      height: Math.max(1, height),
      channels: 4,
      background: { r: 255, g: 255, b: 255, alpha: 1 },
    },
    limitInputPixels: Math.max(height * width * 2, 10000 * 10000),
  })
    .composite(compositeOperations)
    .jpeg({ quality: JPEG_QUALITY, mozjpeg: true });

  const resultBuffer = await finalImage.toBuffer();
  console.log(
    `[Screenshot] Final image created (JPEG format). Size: ${(resultBuffer.length / 1024 / 1024).toFixed(2)}MB`
  );

  return resultBuffer;
}

async function getPageHeight(page) {
  const height = await page.evaluate(
    () => document.documentElement.scrollHeight
  );
  console.log(`[Screenshot] Page scrollHeight: ${height}px`);
  return height;
}
