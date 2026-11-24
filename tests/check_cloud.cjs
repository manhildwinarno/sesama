// NODE_PATH=<Playwright location> node tests/check_cloud.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
  try {
    const page = await browser.newPage();
    const forbidden = [];
    page.on('request', r => {if (/127\.0\.0\.1:\d+\/frame/.test(r.url())) forbidden.push(r.url());});
    await page.goto(process.env.APP_URL || 'http://localhost:8512');
    await page.getByRole('button',{name:'START',exact:true}).click();
    await page.getByText('Diagnostics',{exact:true}).click();
    await page.waitForFunction(() => /Last frame 0\.[0-9]s ago · [1-9]/.test(document.body.textContent), {timeout:30000});
    const track = await page.locator('video').evaluateHandle(v => v.srcObject.getVideoTracks()[0]);
    const isolated = await browser.newPage();
    await isolated.goto(process.env.APP_URL || 'http://localhost:8512');
    await isolated.getByText('Diagnostics',{exact:true}).click();
    await isolated.getByText(/Last frame none/).waitFor();
    await page.getByRole('button',{name:'Mirror preview',exact:true}).click();
    const mirror = page.getByRole('button',{name:'Mirror preview',exact:true});
    const landmarks = page.getByRole('button',{name:'Show hand landmarks',exact:true});
    for (const control of [mirror, landmarks, page.getByRole('button',{name:'STOP',exact:true})]) {
      await control.hover();
      assert(await control.evaluate(e => e.matches(':hover') && getComputedStyle(e).transitionDuration.includes('0.18s')), 'Dock hover/transition missing');
    }
    await page.locator('video[style*="transform: none"]').waitFor();
    assert.equal(await mirror.getAttribute('aria-pressed'), 'false');
    await landmarks.click();
    await page.locator('.landmarks[aria-pressed="true"]').waitFor();
    await mirror.click();
    await page.locator('video[style*="scaleX(-1)"]').waitFor();
    assert.equal(await mirror.getAttribute('aria-pressed'), 'true');
    assert.equal(await landmarks.getAttribute('aria-pressed'), 'true');
    assert.equal(await track.evaluate(t => t.readyState), 'live');
    await page.getByRole('radio',{name:'BISINDO',exact:true}).click();
    await page.getByRole('button',{name:'START',exact:true}).waitFor();
    assert.equal(await track.evaluate(t => t.readyState), 'ended');
    await page.getByRole('button',{name:'START',exact:true}).click();
    const bisindoTrack = await page.locator('video').evaluateHandle(v => v.srcObject.getVideoTracks()[0]);
    await page.getByRole('link',{name:/Text to graphics/}).click();
    await page.getByRole('textbox',{name:'Text to spell',exact:true}).waitFor();
    assert.equal(await bisindoTrack.evaluate(t => t.readyState), 'ended');
    assert.deepEqual(forbidden, []);
    console.log('PASS: sustained Streamlit frames, isolated sessions, controls preserve camera, navigation closes track, no loopback requests.');
  } finally {await browser.close();}
})().catch(e => {console.error(e);process.exitCode=1;});
