// Capture the actual presentation canvas, without browser chrome or slide controls.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');

async function main() {
  const output = process.argv[2];
  if (!output) throw new Error('Usage: node capture_ppt.cjs <build/assets directory>');
  fs.mkdirSync(output, {recursive:true});
  const executablePath = process.env.CHROME_PATH;
  const browser = await chromium.launch({headless:true, ...(executablePath ? {executablePath} : {})});
  try {
    const page = await browser.newPage({viewport:{width:1920,height:1192},reducedMotion:'reduce',deviceScaleFactor:1});
    const entry = pathToFileURL(path.join(__dirname,'../分享演示/index.html')).href;
    for (const number of [4,6,10]) {
      await page.goto(`${entry}#${number}`);
      await page.locator('.slide:not([hidden])').waitFor();
      await page.locator('#stage').screenshot({path:path.join(output,`ppt${number}.png`)});
      console.log(`Captured PPT slide ${number}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch(error=>{console.error(error);process.exitCode=1;});
