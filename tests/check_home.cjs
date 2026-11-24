// NODE_PATH=<Playwright location> APP_URL=http://localhost:8519 node tests/check_home.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch();
 try {
  for(const width of [1440,390]) {
   const page=await browser.newPage({viewport:{width,height:900}});
   const errors=[]; page.on('pageerror',e=>errors.push(e.message));
   await page.goto(process.env.APP_URL || 'http://localhost:8519');
   await page.getByRole('heading',{name:'Every letter. A little closer.'}).waitFor();
   assert.equal(await page.locator('video').count(),0,'Home must not mount camera');
   await page.getByTestId('stSidebar').waitFor({state:'hidden'});
    assert.equal(await page.locator('.hero-demo, .hero-eyebrow, .landing-note').count(),0);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Home overflows viewport');
    const main=page.getByTestId('stMain');
    assert(await main.evaluate(el=>getComputedStyle(el).scrollbarGutter==='stable'));
    const mainBox=await main.boundingBox();
    const margin=width<768?8:16;
    assert(Math.abs(mainBox.x-margin)<=1 && Math.abs(width-mainBox.x-mainBox.width-margin)<=1,'Panel needs equal left/right viewport margins');
    const heroBox=await page.locator('.st-key-landing-hero').boundingBox();
    assert(heroBox.x+heroBox.width<=mainBox.x+mainBox.width-20,'Hero needs clearance from scrollbar');
   await page.screenshot({path:`logs/design/home-${width}.png`,fullPage:true});
    if(width<900) await page.locator('.mobile-nav summary').click();
    const links=page.locator(width<900?'.mobile-nav':'.desktop-links');
    for(const anchor of ['how-it-works','benchmark','benefits','faq']) {
     await links.locator(`a[href="#${anchor}"]`).click();
     await page.waitForFunction(id=>location.hash==='#'+id,anchor);
     const box=await page.locator('#'+anchor).boundingBox();
     assert(box.y>=0 && box.y<900,'Anchor target must scroll into view');
    }
    await page.locator('.nav-launch').click();
    await page.getByRole('button',{name:'START',exact:true}).waitFor();
    assert(new URL(page.url()).pathname==='/sign-to-text');
   await page.goto(process.env.APP_URL || 'http://localhost:8519');
   await page.getByRole('button',{name:/Try sign to text/}).click();
   await page.getByRole('button',{name:'START',exact:true}).waitFor();
   assert(new URL(page.url()).pathname==='/sign-to-text');
   assert.deepEqual(errors,[]);
   await page.close();
  }
   console.log('PASS: desktop/mobile home, no illustration/camera, section anchors, menu, workspace link and hero CTA.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
