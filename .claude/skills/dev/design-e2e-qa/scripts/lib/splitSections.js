import { mkdir } from 'node:fs/promises';
import { basename, dirname, extname, join } from 'node:path';
import sharp from 'sharp';

const SECTION_SELECTORS = 'section, header, footer, main > div, [class*="section"], [role="log"]';

/**
 * DOM構造に基づいてスクリーンショットをセクション単位で分割する。
 *
 * @param {import('puppeteer').Page} page
 * @param {Buffer} screenshotBuffer
 * @param {string} outputPath
 * @returns {Promise<Array<{fileName: string, id: string, top: number, left: number, width: number, height: number}>>}
 */
export async function splitByDom(page, screenshotBuffer, outputPath) {
  const metadata = await sharp(screenshotBuffer).metadata();
  const imageWidth = metadata.width;
  const imageHeight = metadata.height;

  if (!imageWidth || !imageHeight) {
    throw new Error('Unable to read screenshot dimensions for section splitting.');
  }

  const sections = await page.evaluate((selectors) => {
    const sanitizeId = (value) =>
      String(value || '')
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_-]+/g, '-')
        .replace(/^-+|-+$/g, '');

    return Array.from(document.querySelectorAll(selectors))
      .map((el, index) => {
        const rect = el.getBoundingClientRect();
        const tag = el.tagName.toLowerCase();
        const className =
          typeof el.className === 'string'
            ? el.className.split(/\s+/).filter(Boolean)[0]
            : '';
        const rawId = el.id || className || `${tag}-${index + 1}`;
        return {
          id: sanitizeId(rawId) || `${tag}-${index + 1}`,
          top: Math.round(rect.top + window.scrollY),
          left: Math.round(rect.left + window.scrollX),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
        };
      })
      .filter((section) => section.height > 50 && section.width > 0);
  }, SECTION_SELECTORS);

  const outputDir = dirname(outputPath);
  const extension = extname(outputPath) || '.jpg';
  const baseName = basename(outputPath, extension);
  await mkdir(outputDir, { recursive: true });

  const savedSections = [];

  for (const [index, section] of sections.entries()) {
    const left = clamp(section.left, 0, imageWidth - 1);
    const top = clamp(section.top, 0, imageHeight - 1);
    const width = clamp(section.width, 1, imageWidth - left);
    const height = clamp(section.height, 1, imageHeight - top);

    if (width <= 0 || height <= 0) {
      continue;
    }

    const fileName = `${baseName}-section-${String(index + 1).padStart(2, '0')}-${section.id}${extension}`;
    const filePath = join(outputDir, fileName);

    await sharp(screenshotBuffer)
      .extract({ left, top, width, height })
      .jpeg({ quality: 85, mozjpeg: true })
      .toFile(filePath);

    savedSections.push({
      fileName,
      id: section.id,
      top,
      left,
      width,
      height,
    });
  }

  return savedSections;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
