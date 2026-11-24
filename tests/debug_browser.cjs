// Run with NODE_PATH pointing to installed Playwright. Synthetic webcam only.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});
 const page = await browser.newPage();
 let posts=0;
 page.on('pageerror', e=>console.log('JS_ERROR',e.message));
 page.on('requestfailed', r=>console.log('REQUEST_FAILED',r.url(),r.failure()));
 page.on('response', r=>{if(r.url().endsWith('/frame')) {posts++; if(r.status()!==200 && r.status()!==204) console.log('HTTP',r.status());}});
 try {
  await page.goto(process.env.APP_URL || 'http://localhost:8511');
  await page.getByRole('button',{name:'START',exact:true}).click({timeout:90000});
  for(let i=0;i<5;i++) {
   await page.waitForTimeout(3000);
   console.log('SAMPLE',i,'posts',posts,await page.locator('video').evaluate(v=>({width:v.videoWidth,paused:v.paused,track:v.srcObject?.getVideoTracks()[0]?.readyState})));
  }
  await page.getByRole('button',{name:'STOP',exact:true}).click();
  await page.getByRole('button',{name:'START',exact:true}).click();
  await page.waitForTimeout(3000);
  console.log('RESTART_POSTS',posts);
   for(const label of ['Show hand landmarks','Mirror preview']) {
    await page.getByRole('button',{name:label,exact:true}).click();
   await page.waitForTimeout(3000);
   console.log('TOGGLE',label,'posts',posts,await page.locator('video').evaluate(v=>({paused:v.paused,track:v.srcObject?.getVideoTracks()[0]?.readyState})));
  }
   await page.getByText('Diagnostics',{exact:true}).click();
   console.log('DIAGNOSTICS',await page.getByText(/Last frame/).textContent());
  for(let i=0;i<12;i++) {
   const previous=posts;
   await page.waitForTimeout(5000);
   assert(posts>previous,'Frame delivery stalled');
   assert(await page.locator('video').evaluate(v=>v.srcObject?.getVideoTracks()[0]?.readyState==='live'),'Camera stopped');
    console.log('LONG',i,posts,await page.getByText(/Last frame/).textContent());
   console.log('STATE',await page.locator('video').evaluate(v=>{const s=v.getRootNode().cameraState;return {hidden:document.hidden,stream:!!s?.stream,timer:s?.timer,raf:s?.raf,inflight:s?.inflight,paused:v.paused,connected:v.isConnected}}));
  }
  // Render known landmarks through actual HTTP response handling, independent of ML accuracy.
  await page.route('**/frame',async route=>{
   if(route.request().method()!=='POST') return route.continue();
   const response=await route.fetch();
   const payload=await response.json();
   payload.overlay={points:[Array.from({length:21},()=>[0.25,0.5])],stamp:Date.now(),flip:false};
   await route.fulfill({response,json:payload});
  });
  await page.waitForTimeout(1500);
  assert(await page.locator('canvas').evaluate(c=>c.getContext('2d').getImageData(c.width*.25,c.height*.5,1,1).data[3]>0),'Landmarks not painted');
  await page.getByRole('button',{name:'STOP',exact:true}).click();
  await page.getByRole('button',{name:'START',exact:true}).click();
  await page.waitForTimeout(2000);
  assert(await page.locator('canvas').evaluate(c=>c.getContext('2d').getImageData(c.width*.25,c.height*.5,1,1).data[3]>0),'Landmarks missing after restart');
  console.log('PASS: sustained capture, toggles, restart, HTTP overlay rendering');
 } finally {await browser.close();}
})();
