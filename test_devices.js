const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const devices = [
  { name: 'desktop_1440x900', width: 1440, height: 900, isMobile: false },
  { name: 'ipad_landscape_1024x768', width: 1024, height: 768, isMobile: true, hasTouch: true },
  { name: 'ipad_portrait_768x1024', width: 768, height: 1024, isMobile: true, hasTouch: true },
  { name: 'iphone_mobile_390x844', width: 390, height: 844, isMobile: true, hasTouch: true }
];

async function run() {
  const outDir = path.join(__dirname, 'screenshots');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  const browser = await chromium.launch({ headless: true });
  console.log('Browser launched successfully.');

  let totalErrors = 0;

  for (const dev of devices) {
    const context = await browser.newContext({
      viewport: { width: dev.width, height: dev.height },
      isMobile: dev.isMobile,
      hasTouch: dev.hasTouch
    });
    const page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`[${dev.name}] Console Error:`, msg.text());
        totalErrors++;
      }
    });

    page.on('dialog', async dialog => {
      console.log(`[${dev.name}] Dialog intercepted: "${dialog.message().substring(0, 30)}..." -> Accepting`);
      await dialog.accept();
    });

    console.log(`\n--- Testing ${dev.name} (${dev.width}x${dev.height}) ---`);

    // 1. TEST LANDING PAGE (index.html) - DEFAULT DARK
    console.log(`[${dev.name}] Testing Landing Page (Dark)...`);
    await page.goto('http://127.0.0.1:8081/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);

    const shotLandingDark = path.join(outDir, `${dev.name}_landing_dark.png`);
    await page.screenshot({ path: shotLandingDark, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotLandingDark}`);

    // 2. TEST THEME TOGGLE ON LANDING PAGE (Dark -> Light)
    console.log(`[${dev.name}] Toggling Landing Page Theme to Light...`);
    await page.click('#btn-theme-toggle');
    await page.waitForTimeout(500);
    const isLight = await page.$eval('body', b => b.classList.contains('light-theme'));
    if (!isLight) throw new Error('Failed to switch to light-theme on landing page!');
    const shotLandingLight = path.join(outDir, `${dev.name}_landing_light.png`);
    await page.screenshot({ path: shotLandingLight, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotLandingLight}`);

    // 3. TEST LANGUAGE TOGGLE ON LANDING PAGE (DE -> EN)
    console.log(`[${dev.name}] Toggling Landing Page Language to EN...`);
    await page.click('#btn-lang-toggle');
    await page.waitForTimeout(500);
    const enTitle = await page.$eval('.hero-title', el => el.textContent.trim());
    console.log(`  ✓ English Headline verified: "${enTitle}"`);
    if (!enTitle.includes('Real-Time Mediterranean')) {
      throw new Error(`Expected English headline, got: "${enTitle}"`);
    }

    // 4. TEST DEEP-LINK NAVIGATION TO RADAR
    console.log(`[${dev.name}] Deep-linking to radar.html?sector=central_med...`);
    await page.click('#card-sector-central');
    await page.waitForTimeout(1500);

    const currentUrl = page.url();
    console.log(`  ✓ Navigated to: ${currentUrl}`);
    if (!currentUrl.includes('radar.html')) {
      throw new Error(`Expected URL to contain radar.html, got ${currentUrl}`);
    }

    // 5. TEST RADAR THEME SWITCH (Light -> Dark)
    console.log(`[${dev.name}] Testing Radar Dark Theme switch...`);
    await page.click('#btn-theme-toggle');
    await page.waitForTimeout(500);
    const shotRadarDark = path.join(outDir, `${dev.name}_radar_dark.png`);
    await page.screenshot({ path: shotRadarDark, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotRadarDark}`);

    // 6. TEST COLLAPSIBLE ADVOCACY TOOLKIT IN RADAR
    console.log(`[${dev.name}] Testing collapsible Advocacy Toolkit drawer...`);
    const advCard = await page.$('#advocacy-toolkit-card');
    if (advCard) {
      await page.click('#advocacy-toolkit-card summary');
      await page.waitForTimeout(300);
      console.log('  ✓ Advocacy Toolkit expanded successfully.');
    }

    // 7. TEST BRIDGE MODE
    console.log(`[${dev.name}] Testing Bridge Mode in Radar...`);
    await page.click('#prof-btn-bridge');
    await page.waitForTimeout(1000);
    const shotRadarBridge = path.join(outDir, `${dev.name}_radar_bridge.png`);
    await page.screenshot({ path: shotRadarBridge, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotRadarBridge}`);

    // 8. TEST RETURN TO HOME LINK
    console.log(`[${dev.name}] Returning to Home...`);
    const homeLink = await page.$('a[href="index.html"]');
    if (!homeLink) throw new Error('Home return link not found!');
    await homeLink.click();
    await page.waitForTimeout(1000);
    console.log(`  ✓ Successfully back at: ${page.url()}`);

    await context.close();
  }

  await browser.close();
  console.log(`\nAll device & interaction tests completed successfully. Total console errors: ${totalErrors}`);
  if (totalErrors > 0) {
    process.exit(1);
  }
}

run().catch(err => {
  console.error('Error during test execution:', err);
  process.exit(1);
});
