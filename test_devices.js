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

  for (const dev of devices) {
    const context = await browser.newContext({
      viewport: { width: dev.width, height: dev.height },
      isMobile: dev.isMobile,
      hasTouch: dev.hasTouch
    });
    const page = await context.newPage();

    // Listen to console errors
    page.on('console', msg => {
      if (msg.type() === 'error') console.log(`[${dev.name}] Console Error:`, msg.text());
    });

    console.log(`Testing ${dev.name} (${dev.width}x${dev.height})...`);
    await page.goto('http://127.0.0.1:8081/', { waitUntil: 'networkidle', timeout: 15000 });
    
    // Wait for map and charts to settle in default Public mode
    await page.waitForTimeout(1500);

    const shotPath = path.join(outDir, `${dev.name}.png`);
    await page.screenshot({ path: shotPath, fullPage: false });
    console.log(`Saved screenshot (Public mode): ${shotPath}`);

    // Switch to Bridge mode and test
    console.log(`[${dev.name}] Switching to Bridge Mode...`);
    await page.click('#prof-btn-bridge');
    await page.waitForTimeout(1000);

    const shotPathBridge = path.join(outDir, `${dev.name}_bridge.png`);
    await page.screenshot({ path: shotPathBridge, fullPage: false });
    console.log(`Saved screenshot (Bridge mode): ${shotPathBridge}`);

    await context.close();
  }

  await browser.close();
  console.log('All device tests completed successfully.');
}

run().catch(err => {
  console.error('Error during test execution:', err);
  process.exit(1);
});
