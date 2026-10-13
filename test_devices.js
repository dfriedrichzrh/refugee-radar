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

    // 1. TEST LANDING PAGE (index.html) - DEFAULT LIGHT & ENGLISH (Clean Precision)
    console.log(`[${dev.name}] Testing Landing Page (Default Light & EN)...`);
    await page.goto('http://127.0.0.1:8081/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);

    const isDefaultLight = await page.$eval('body', b => b.classList.contains('light-theme'));
    if (!isDefaultLight) throw new Error('Expected landing page to default to light-theme!');
    
    const defaultTitle = await page.$eval('.hero-title', el => el.textContent.trim());
    console.log(`  ✓ Default English Headline verified: "${defaultTitle}"`);
    if (!defaultTitle.includes('Real-Time Mediterranean')) {
      throw new Error(`Expected default English headline, got: "${defaultTitle}"`);
    }

    const shotLandingLight = path.join(outDir, `${dev.name}_landing_light.png`);
    await page.screenshot({ path: shotLandingLight, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotLandingLight}`);

    // 2. TEST THEME TOGGLE ON LANDING PAGE (Light -> Dark)
    console.log(`[${dev.name}] Toggling Landing Page Theme to Dark...`);
    await page.click('#btn-theme-toggle');
    await page.waitForTimeout(500);
    const isDark = await page.$eval('body', b => b.classList.contains('dark-theme'));
    if (!isDark) throw new Error('Failed to switch to dark-theme on landing page!');
    const shotLandingDark = path.join(outDir, `${dev.name}_landing_dark.png`);
    await page.screenshot({ path: shotLandingDark, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotLandingDark}`);

    // Toggle back to Light for remaining tests
    await page.click('#btn-theme-toggle');
    await page.waitForTimeout(300);

    // 3. TEST LANGUAGE TOGGLE ON LANDING PAGE (EN -> DE -> EN)
    console.log(`[${dev.name}] Toggling Landing Page Language to DE...`);
    await page.click('#btn-lang-toggle');
    await page.waitForTimeout(500);
    const deTitle = await page.$eval('.hero-title', el => el.textContent.trim());
    console.log(`  ✓ German Headline verified: "${deTitle}"`);
    if (!deTitle.includes('Echtzeit-Lagebild')) {
      throw new Error(`Expected German headline, got: "${deTitle}"`);
    }

    // Toggle back to EN
    await page.click('#btn-lang-toggle');
    await page.waitForTimeout(300);

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

    // 6. TEST STREAMLINED SITREP MODAL & INTEGRATED GPX EXPORT
    console.log(`[${dev.name}] Testing SITREP Modal and Integrated GPX Export...`);
    await page.click('#lbl-report-bar');
    await page.waitForTimeout(600);
    const sitrepModal = await page.$('#sitrep-modal.active');
    if (!sitrepModal) throw new Error('SITREP modal failed to open!');
    const gpxBtn = await page.$('#sitrep-modal button[onclick*="exportNauticalGpx"]');
    if (!gpxBtn) throw new Error('GPX export button missing from SITREP modal!');
    console.log('  ✓ SITREP modal and integrated GPX export verified.');

    const shotRadarSitrep = path.join(outDir, `${dev.name}_radar_sitrep.png`);
    await page.screenshot({ path: shotRadarSitrep, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotRadarSitrep}`);

    // Close SITREP modal via Escape key
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // 7. TEST STREAMLINED LEAN RADAR DASHBOARD
    console.log(`[${dev.name}] Verifying Lean Radar Dashboard layout...`);
    const shotRadarClean = path.join(outDir, `${dev.name}_radar_clean.png`);
    await page.screenshot({ path: shotRadarClean, fullPage: false });
    console.log(`  ✓ Screenshot: ${shotRadarClean}`);

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
