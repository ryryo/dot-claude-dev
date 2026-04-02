/**
 * waitForMedia.js - メディア要素（動画・画像）の読み込み待機
 *
 * 動画要素や画像要素が完全に読み込まれるまで待機する
 */

/**
 * ファーストビュー（ビューポート内）の画像を強制的に読み込む
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 * @param {number} [timeout=10000] - タイムアウト時間（ミリ秒）
 */
export async function waitForFirstViewImages(page, timeout = 10000) {
  console.log('[Media] Waiting for first-view images to load...');

  try {
    const imageInfo = await page.evaluate(async (timeout) => {
      const viewportHeight = window.innerHeight;
      const images = Array.from(document.querySelectorAll('img'));

      const firstViewImages = images.filter((img) => {
        const rect = img.getBoundingClientRect();
        return rect.top < viewportHeight && rect.bottom > 0;
      });

      if (firstViewImages.length === 0) {
        return { total: 0, loaded: 0, forced: 0 };
      }

      console.log(
        `[Browser] Found ${firstViewImages.length} first-view image(s)`
      );

      let forcedCount = 0;

      const loadPromises = firstViewImages.map((img, index) => {
        return new Promise((resolve) => {
          if (img.loading === 'lazy') {
            img.loading = 'eager';
            console.log(`[Browser] First-view image ${index + 1}: Changed lazy to eager`);
          }

          const dataSrc = img.getAttribute('data-src') || img.getAttribute('data-lazy-src');
          if (dataSrc && !img.src) {
            img.src = dataSrc;
            console.log(`[Browser] First-view image ${index + 1}: Set src from data-src`);
            forcedCount++;
          }

          if (img.complete && img.naturalWidth > 0) {
            console.log(`[Browser] First-view image ${index + 1}: Already loaded (${img.naturalWidth}x${img.naturalHeight})`);
            resolve(true);
            return;
          }

          if (img.complete && img.naturalWidth === 0 && img.src) {
            console.log(`[Browser] First-view image ${index + 1}: Force reloading (was complete but empty)`);
            const originalSrc = img.src;
            img.src = '';
            setTimeout(() => {
              img.src = originalSrc;
            }, 10);
            forcedCount++;
          }

          let resolved = false;

          const onLoad = () => {
            if (resolved) return;
            resolved = true;
            console.log(`[Browser] First-view image ${index + 1}: Load event fired`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(true);
          };

          const onError = () => {
            if (resolved) return;
            resolved = true;
            console.warn(`[Browser] First-view image ${index + 1}: Failed to load`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(false);
          };

          img.addEventListener('load', onLoad);
          img.addEventListener('error', onError);

          setTimeout(() => {
            if (resolved) return;
            resolved = true;
            console.warn(`[Browser] First-view image ${index + 1}: Load timeout`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(false);
          }, timeout);
        });
      });

      const results = await Promise.all(loadPromises);
      const loadedCount = results.filter((r) => r === true).length;

      return { total: firstViewImages.length, loaded: loadedCount, forced: forcedCount };
    }, timeout);

    if (imageInfo.total > 0) {
      console.log(
        `[Media] First-view: ${imageInfo.loaded}/${imageInfo.total} image(s) loaded (${imageInfo.forced} force-reloaded)`
      );
    } else {
      console.log('[Media] No first-view images found');
    }
  } catch (error) {
    console.warn(`[Media] Error waiting for first-view images: ${error.message}`);
  }

  await new Promise((resolve) => setTimeout(resolve, 1500));
}

/**
 * 画像要素の読み込みを待機
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 * @param {number} [timeout=10000] - タイムアウト時間（ミリ秒）
 */
export async function waitForImages(page, timeout = 10000) {
  console.log('[Media] Waiting for image elements to load...');

  try {
    const imageInfo = await page.evaluate(async (timeout) => {
      const images = Array.from(document.querySelectorAll('img'));
      if (images.length === 0) {
        return { total: 0, loaded: 0 };
      }

      console.log(`[Browser] Found ${images.length} image element(s)`);

      const loadPromises = images.map((img, index) => {
        return new Promise((resolve) => {
          if (img.complete && img.naturalWidth > 0) {
            console.log(`[Browser] Image ${index + 1} already loaded`);
            resolve(true);
            return;
          }

          if (img.complete && img.naturalWidth === 0) {
            console.warn(`[Browser] Image ${index + 1} failed to load (naturalWidth=0)`);
            resolve(false);
            return;
          }

          let resolved = false;

          const onLoad = () => {
            if (resolved) return;
            resolved = true;
            console.log(`[Browser] Image ${index + 1} load event fired`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(true);
          };

          const onError = () => {
            if (resolved) return;
            resolved = true;
            console.warn(`[Browser] Image ${index + 1} failed to load`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(false);
          };

          img.addEventListener('load', onLoad);
          img.addEventListener('error', onError);

          setTimeout(() => {
            if (resolved) return;
            resolved = true;
            console.warn(`[Browser] Image ${index + 1} load timeout`);
            img.removeEventListener('load', onLoad);
            img.removeEventListener('error', onError);
            resolve(false);
          }, timeout);

          if (img.loading === 'lazy' && img.src) {
            img.loading = 'eager';
          }
        });
      });

      const results = await Promise.all(loadPromises);
      const loadedCount = results.filter((r) => r === true).length;

      return { total: images.length, loaded: loadedCount };
    }, timeout);

    if (imageInfo.total > 0) {
      console.log(
        `[Media] ${imageInfo.loaded}/${imageInfo.total} image element(s) loaded`
      );
    } else {
      console.log('[Media] No image elements found');
    }
  } catch (error) {
    console.warn(`[Media] Error waiting for images: ${error.message}`);
  }

  await new Promise((resolve) => setTimeout(resolve, 1500));
}

/**
 * CSS背景画像の読み込みを待機
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 */
export async function waitForBackgroundImages(page) {
  console.log('[Media] Waiting for background images to load...');

  try {
    await page.evaluate(() => {
      const allElements = document.querySelectorAll('*');
      const bgImages = new Set();

      allElements.forEach((el) => {
        const style = window.getComputedStyle(el);
        const bgImage = style.backgroundImage;
        if (bgImage && bgImage !== 'none') {
          const match = bgImage.match(/url\(["']?([^"']+)["']?\)/);
          if (match && match[1]) {
            bgImages.add(match[1]);
          }
        }
      });

      if (bgImages.size > 0) {
        console.log(`[Browser] Found ${bgImages.size} background image(s)`);
      }

      const loadPromises = Array.from(bgImages).map((url, index) => {
        return new Promise((resolve) => {
          const img = new Image();
          img.onload = () => {
            console.log(`[Browser] Background image ${index + 1} loaded`);
            resolve();
          };
          img.onerror = () => {
            console.warn(`[Browser] Background image ${index + 1} failed to load`);
            resolve();
          };
          img.src = url;
        });
      });

      return Promise.all(loadPromises);
    });

    await new Promise((resolve) => setTimeout(resolve, 1000));
  } catch (error) {
    console.warn(`[Media] Error waiting for background images: ${error.message}`);
  }
}

/**
 * 動画要素の読み込みを待機（poster画像も含む）
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 * @param {number} [timeout=15000] - タイムアウト時間（ミリ秒）
 */
export async function waitForVideos(page, timeout = 15000) {
  console.log('[Media] Waiting for video elements to load...');

  try {
    const videoInfo = await page.evaluate(async (timeout) => {
      const videos = Array.from(document.querySelectorAll('video'));
      if (videos.length === 0) {
        return { total: 0, loaded: 0, posterLoaded: 0, retried: 0 };
      }

      console.log(`[Browser] Found ${videos.length} video element(s)`);

      let lazyLoadFixed = 0;
      let debugCount = 0;
      videos.forEach((video, index) => {
        if (debugCount < 3) {
          const source = video.querySelector('source');
          console.log(`[Browser] Video ${index + 1} DEBUG: readyState=${video.readyState}, src="${video.src || 'EMPTY'}", currentSrc="${video.currentSrc || 'EMPTY'}", source.src="${source?.src || 'NO SOURCE'}", has data-src=${!!source?.getAttribute('data-src')}`);
          debugCount++;
        }
        let videoNeedsReload = false;

        const videoDataSrc = video.getAttribute('data-src');
        if (videoDataSrc && (!video.src || video.src === '')) {
          console.log(`[Browser] Video ${index + 1}: Setting src from data-src (${videoDataSrc})`);
          video.src = videoDataSrc;
          lazyLoadFixed++;
          videoNeedsReload = true;
        }

        const sources = video.querySelectorAll('source');
        sources.forEach((source, si) => {
          const sourceDataSrc = source.getAttribute('data-src');
          if (sourceDataSrc && (!source.src || source.src === '')) {
            console.log(`[Browser] Video ${index + 1} source ${si + 1}: Setting src from data-src (${sourceDataSrc.substring(0, 50)}...)`);
            source.src = sourceDataSrc;
            lazyLoadFixed++;
            videoNeedsReload = true;
          }
        });

        if (video.classList.contains('lazyload')) {
          video.classList.remove('lazyload');
          video.classList.add('lazyloaded');
        }

        if (videoNeedsReload) {
          video.load();
        }
      });

      if (lazyLoadFixed > 0) {
        console.log(`[Browser] Fixed ${lazyLoadFixed} lazy-loaded video/source elements`);
        await new Promise((r) => setTimeout(r, 2000));
      }

      console.log(`[Browser] Force-rendering all videos by play+pause...`);
      for (let i = 0; i < videos.length; i++) {
        const video = videos[i];
        if (video.readyState >= 2) {
          try {
            video.muted = true;
            const playPromise = video.play();
            if (playPromise) {
              await playPromise;
            }
            await new Promise((r) => setTimeout(r, 100));
            video.pause();
            video.currentTime = 0;
            console.log(`[Browser] Video ${i + 1}: Force-rendered (readyState=${video.readyState})`);
          } catch (e) {
            console.log(`[Browser] Video ${i + 1}: Could not play (${e.message})`);
          }
        }
      }
      await new Promise((r) => setTimeout(r, 1000));

      let posterLoadedCount = 0;
      let videoLoadedCount = 0;

      const loadPromises = videos.map((video, index) => {
        return new Promise(async (resolve) => {
          const startTime = Date.now();
          let resolved = false;

          const finish = (reason) => {
            if (resolved) return;
            resolved = true;
            console.log(`[Browser] Video ${index + 1}: ${reason} (${Date.now() - startTime}ms)`);
            resolve();
          };

          const timeoutId = setTimeout(() => {
            finish('timeout');
          }, timeout);

          const cleanup = () => {
            clearTimeout(timeoutId);
          };

          console.log(`[Browser] Video ${index + 1}: Scrolling into view`);
          video.scrollIntoView({ block: 'center', behavior: 'instant' });
          await new Promise((r) => setTimeout(r, 500));

          if (video.poster) {
            console.log(`[Browser] Video ${index + 1}: Loading poster image...`);

            const posterLoaded = await new Promise((posterResolve) => {
              const posterImg = new Image();

              posterImg.onload = () => {
                console.log(`[Browser] Video ${index + 1}: Poster loaded (${posterImg.naturalWidth}x${posterImg.naturalHeight})`);
                posterResolve(true);
              };
              posterImg.onerror = () => {
                console.warn(`[Browser] Video ${index + 1}: Poster failed to load`);
                posterResolve(false);
              };
              posterImg.src = video.poster;
            });

            if (posterLoaded) {
              posterLoadedCount++;
            }
          }

          if (video.readyState >= 2) {
            videoLoadedCount++;
            cleanup();
            finish(`loaded (readyState=${video.readyState})`);
            return;
          }

          const onLoadedData = () => {
            cleanup();
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('error', onError);
            videoLoadedCount++;
            finish('loadeddata event');
          };

          const onError = () => {
            cleanup();
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('error', onError);
            finish('error event');
          };

          video.addEventListener('loadeddata', onLoadedData);
          video.addEventListener('error', onError);

          try {
            video.load();
          } catch (error) {
            console.warn(`[Browser] Video ${index + 1}: load() failed (${error.message})`);
          }
        });
      });

      await Promise.all(loadPromises);

      return {
        total: videos.length,
        loaded: videoLoadedCount,
        posterLoaded: posterLoadedCount,
        retried: lazyLoadFixed,
      };
    }, timeout);

    if (videoInfo.total > 0) {
      console.log(
        `[Media] ${videoInfo.loaded}/${videoInfo.total} video(s) loaded, ${videoInfo.posterLoaded} poster(s) loaded, ${videoInfo.retried} lazy source(s) retried`
      );
    } else {
      console.log('[Media] No video elements found');
    }
  } catch (error) {
    console.warn(`[Media] Error waiting for videos: ${error.message}`);
  }

  await new Promise((resolve) => setTimeout(resolve, 1000));
}

/**
 * すべてのメディア要素の読み込みを待機
 * @param {import('puppeteer').Page} page - Puppeteer Page オブジェクト
 */
export async function waitForAllMedia(page) {
  await waitForFirstViewImages(page);
  await waitForImages(page);
  await waitForBackgroundImages(page);
  await waitForVideos(page);
}
