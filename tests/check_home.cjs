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
   assert(await page.locator('.hero-demo img').evaluateAll(images=>images.every(i=>i.complete && i.naturalWidth>0)));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Home overflows viewport');
   await page.screenshot({path:`logs/design/home-${width}.png`,fullPage:true});
   await page.getByRole('button',{name:/Explore letter graphics/}).click();
   await page.getByRole('textbox',{name:'Text to spell',exact:true}).waitFor();
   assert(new URL(page.url()).pathname==='/text-to-graphics');
   await page.goto(process.env.APP_URL || 'http://localhost:8519');
   await page.getByRole('button',{name:/Try sign to text/}).click();
   await page.getByRole('button',{name:'START',exact:true}).waitFor();
   assert(new URL(page.url()).pathname==='/sign-to-text');
   assert.deepEqual(errors,[]);
   await page.close();
  }
  console.log('PASS: desktop/mobile home, no camera, English routes, both hero actions.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
