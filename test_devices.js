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

    console.log(`\n--- Testing ${dev.name} (${dev.width}x${dev.height}) ---`);

    // 1. TEST LANDING PAGE (index.html)
    console.log(`[${dev.name}] Navigating to Landing Page (index.html)...`);
    await page.goto('http://127.0.0.1:8081/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    const shotLanding = path.join(outDir, `${dev.name}_landing.png`);
    await page.screenshot({ path: shotLanding, fullPage: false });
    console.log(`  ✓ Saved screenshot: ${shotLanding}`);

    // Verify Title and Hero elements
    const heroTitle = await page.$eval('.hero-title', el => el.textContent.trim());
    console.log(`  ✓ Hero Title verified: "${heroTitle}"`);

    // 2. TEST NAVIGATION TO RADAR (radar.html)
    console.log(`[${dev.name}] Testing deep-link from sector card to radar.html...`);
    await page.click('#card-sector-central');
    await page.waitForTimeout(2000);

    const currentUrl = page.url();
    console.log(`  ✓ Navigated to: ${currentUrl}`);
    if (!currentUrl.includes('radar.html')) {
      throw new Error(`Expected URL to contain radar.html, got ${currentUrl}`);
    }

    const shotRadar = path.join(outDir, `${dev.name}_radar_public.png`);
    await page.screenshot({ path: shotRadar, fullPage: false });
    console.log(`  ✓ Saved screenshot (Radar Public): ${shotRadar}`);

    // 3. TEST BRIDGE MODE SWITCH
    console.log(`[${dev.name}] Testing Bridge Mode switch in Radar...`);
    await page.click('#prof-btn-bridge');
    await page.waitForTimeout(1000);

    const shotRadarBridge = path.join(outDir, `${dev.name}_radar_bridge.png`);
    await page.screenshot({ path: shotRadarBridge, fullPage: false });
    console.log(`  ✓ Saved screenshot (Radar Bridge): ${shotRadarBridge}`);

    // 4. TEST RETURN TO HOME
    console.log(`[${dev.name}] Testing return link to Home...`);
    const homeLink = await page.$('a[href="index.html"]');
    if (!homeLink) throw new Error('Home return link not found in radar.html header!');
    await homeLink.click();
    await page.waitForTimeout(1000);
    console.log(`  ✓ Successfully returned to: ${page.url()}`);

    await context.close();
  }

  await browser.close();
  console.log(`\nAll device tests completed successfully. Total console errors: ${totalErrors}`);
  if (totalErrors > 0) {
    process.exit(1);
  }
}

run().catch(err => {
  console.error('Error during test execution:', err);
  process.exit(1);
});
