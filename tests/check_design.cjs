// NODE_PATH=<Playwright location> node tests/check_design.cjs; synthetic camera only.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({headless:true, args:['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream']});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  fs.mkdirSync('logs/design', {recursive:true});
  try {
    await page.goto(process.env.APP_URL || 'http://localhost:8511');
    await page.getByRole('button', {name:'START',exact:true}).waitFor({timeout:90000});
    await page.evaluate(() => document.fonts.ready);
    assert(await page.evaluate(() => document.fonts.check('14px Inter')), 'Inter not loaded');
    await page.screenshot({path:'logs/design/isyarat-desktop.png',fullPage:true});
    await page.getByRole('button', {name:'START',exact:true}).click();
    await page.waitForFunction(() => {
      return [...document.querySelectorAll('*')].some(e => e.shadowRoot?.querySelector('video')?.srcObject?.active);
    });
    const video = page.locator('video');
    const track = await video.evaluateHandle(v => v.srcObject.getVideoTracks()[0]);
    await page.getByRole('button', {name:/Perluas navigasi/}).click();
    await page.getByRole('button', {name:/Ringkas navigasi/}).waitFor();
    assert(await track.evaluate(t => t.readyState === 'live'), 'Expanding navigation stopped camera');
    await page.getByRole('button', {name:/Ringkas navigasi/}).click();
    await page.getByRole('button', {name:/Perluas navigasi/}).waitFor();
    assert(await track.evaluate(t => t.readyState === 'live'), 'Collapsing navigation stopped camera');
    await page.getByRole('slider', {name:'Batas keyakinan (%)'}).press('ArrowRight');
    assert(await track.evaluate(t => t.readyState === 'live'), 'Settings stopped camera');
    await page.getByRole('link', {name:'Teks ke grafis'}).click();
    await page.getByLabel('Teks yang dieja').fill('IQ AKU!');
    await page.getByLabel('Teks yang dieja').blur();
    await page.getByText('KATA 1 · IQ', {exact:true}).waitFor();
    assert(await track.evaluate(t => t.readyState === 'ended'), 'Navigation leaked camera track');
    await page.screenshot({path:'logs/design/grafis-desktop.png',fullPage:true});
    const mobile = await browser.newPage({viewport:{width:390,height:844}});
    await mobile.goto((process.env.APP_URL || 'http://localhost:8511') + '/grafis');
    await mobile.getByLabel('Teks yang dieja').fill('IQ AKU!');
    await mobile.getByLabel('Teks yang dieja').blur();
    await mobile.getByText('KATA 1 · IQ', {exact:true}).waitFor();
    await mobile.screenshot({path:'logs/design/grafis-mobile.png',fullPage:true});
    assert(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile overflow');
    await mobile.goto(process.env.APP_URL || 'http://localhost:8511');
    await mobile.getByRole('button', {name:'START',exact:true}).waitFor({timeout:90000});
    await mobile.screenshot({path:'logs/design/isyarat-mobile.png',fullPage:true});
    assert(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Camera page mobile overflow');
    await mobile.close();
    await page.getByRole('link', {name:'Panduan'}).click();
    await page.getByText('Kenali abjad, langkah demi langkah.', {exact:true}).waitFor();
    await page.screenshot({path:'logs/design/panduan-desktop.png',fullPage:true});
    assert.deepEqual(errors, []);
    console.log('PASS: font, desktop/mobile screenshots, settings preserve camera, navigation closes track, no JS errors.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode=1;});
