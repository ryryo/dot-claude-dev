/**
 * autoScroll.js - 自動スクロール処理（最重要）
 *
 * LazyLoad画像の読み込みやスクロールアニメーションの発火を
 * 確実に行うための自動スクロール機能
 */

/**
 * @typedef {object} AutoScrollOptions
 * @property {number} [step] - スクロール距離（ピクセル）
 * @property {number} [delay] - 各スクロール後の待機時間（ミリ秒）
 * @property {number} [maxIdleChecks] - ページ高さが変化しない場合の許容回数
 * @property {number} [maxScrolls] - 最大スクロール回数（無限ループ防止）
 * @property {number} [heightCheckDelay] - 高さチェック前の追加待機時間（ミリ秒）
 */

/** @type {Required<AutoScrollOptions>} */
const DEFAULT_OPTIONS = {
  step: 3840,
  delay: 1200,
  maxIdleChecks: 3,
  maxScrolls: 30,
  heightCheckDelay: 600,
};

/**
 * ページを最下部まで自動スクロール
 *
 * LazyLoad画像やスクロールトリガーのアニメーションを発火させるため、
 * 段階的にスクロールを行い、各ステップで待機時間を設ける。
 *
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 * @param {AutoScrollOptions} [options] - スクロールオプション
 * @returns {Promise<{ scrollCount: number }>} - 実行されたスクロール回数
 */
export async function autoScroll(page, options = {}) {
  const { step, delay, maxIdleChecks, maxScrolls, heightCheckDelay } = {
    ...DEFAULT_OPTIONS,
    ...options,
  };

  console.log(`[AutoScroll] Starting auto-scroll...`);
  console.log(
    `[AutoScroll] Options: step=${step}px, delay=${delay}ms, maxScrolls=${maxScrolls}`
  );

  const scrollCount = await page.evaluate(
    async (step, delay, maxIdleChecks, maxScrolls, heightCheckDelay) => {
      return new Promise((resolve) => {
        let totalHeight = 0;
        let idleChecks = 0;
        let scrollCount = 0;
        let lastScrollHeight = document.body.scrollHeight;

        console.log(`[Browser] Initial scrollHeight: ${lastScrollHeight}px`);

        const timer = setInterval(() => {
          const currentScrollTop = window.scrollY;
          console.log(
            `[Browser] Scroll #${scrollCount + 1}: scrollY=${currentScrollTop}px, step=${step}px`
          );

          window.scrollBy(0, step);
          totalHeight += step;
          scrollCount++;

          setTimeout(() => {
            const currentScrollHeight = document.body.scrollHeight;
            const heightChanged = currentScrollHeight > lastScrollHeight;

            console.log(
              `[Browser] Height check: current=${currentScrollHeight}px, previous=${lastScrollHeight}px, changed=${heightChanged}`
            );

            if (heightChanged) {
              lastScrollHeight = currentScrollHeight;
              idleChecks = 0;
            } else {
              idleChecks++;
            }

            const reachedEnd = totalHeight >= currentScrollHeight;
            const idleLimitReached = idleChecks >= maxIdleChecks;
            const maxScrollsReached = scrollCount >= maxScrolls;

            if (reachedEnd || idleLimitReached || maxScrollsReached) {
              let reason = '';
              if (reachedEnd) reason = 'Reached page end';
              else if (idleLimitReached) reason = 'Page height stable';
              else if (maxScrollsReached) reason = 'Max scrolls reached';

              console.log(`[Browser] Stopping scroll. Reason: ${reason}`);
              clearInterval(timer);
              resolve(scrollCount);
            }
          }, heightCheckDelay);
        }, delay);
      });
    },
    step,
    delay,
    maxIdleChecks,
    maxScrolls,
    heightCheckDelay
  );

  console.log(`[AutoScroll] Completed. Total scrolls: ${scrollCount}`);

  await page.evaluate(() => window.scrollTo(0, 0));
  console.log('[AutoScroll] Scrolled back to top.');

  return { scrollCount };
}
