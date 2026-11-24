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
    assert.equal(await page.locator('#how-it-works ol > li').count(),3);
    assert.equal(await page.locator('#how-it-works').getByText('Coming soon.',{exact:true}).count(),0);
    assert.equal(await page.locator('.landing-placeholder').count(),3);
    assert(await page.getByTestId('stMainBlockContainer').evaluate(el=>el.scrollHeight<=el.clientHeight+1),'White panel must contain all sections');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Home overflows viewport');
    const main=page.getByTestId('stMain');
    assert(await main.evaluate(el=>getComputedStyle(el).scrollbarGutter==='stable'));
    const mainBox=await main.boundingBox();
    const margin=width<768?8:16;
    const cardBox=await page.getByTestId('stMainBlockContainer').boundingBox();
    const area=await main.evaluate(el=>({width:el.clientWidth,background:getComputedStyle(el).backgroundColor}));
    assert.equal(area.background,'rgba(0, 0, 0, 0)','Scrollbar container must show gradient, not white');
    assert(Math.abs(mainBox.x)<=1 && Math.abs(mainBox.width-width)<=1,'Scroll area must reach viewport edge');
    assert(Math.abs(cardBox.x-margin)<=1 && Math.abs(area.width-cardBox.x-cardBox.width-margin)<=1,'White card needs equal margins inside scroll area');
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
     if(anchor==='how-it-works') {
      const steps=await page.locator('.how-steps li').all();
      const boxes=await Promise.all(steps.map(step=>step.boundingBox()));
      assert(width<768 ? boxes[1].y>boxes[0].y : Math.abs(boxes[1].y-boxes[0].y)<1,'Steps must stack only on mobile');
      const selection=page.locator('.motion-selection');
       assert(await page.locator('.alphabet-motion .motion-cursor').isVisible(),'Animated cursor must survive HTML sanitization');
       assert.equal(await page.locator('#how-it-works input[type="checkbox"]').count(),0);
       assert(await page.locator('.demo-pose img').evaluate(img=>img.complete && img.naturalWidth>0));
       const pose=await page.locator('.demo-pose').evaluate(el=>{
        const animation=el.getAnimations()[0]; animation.pause();
        animation.currentTime=0; const before=getComputedStyle(el).opacity;
        animation.currentTime=3300; const after=getComputedStyle(el).opacity;
        animation.play(); return [before,after];
       });
       assert.deepEqual(pose,['0','1'],'Step 2 reveals sample pose after Start');
       assert.equal(await page.locator('.demo-start').count(),0);
       assert(await page.locator('.demo-camera img').evaluate(img=>img.complete && img.naturalWidth>0));
       const cameraStates=await page.locator('.camera-motion').evaluate(stage=>{
        const nodes=[stage.querySelector('.demo-camera'),stage.querySelector('.demo-camera-slash')];
        const sample=time=>{
         nodes.forEach(el=>{const a=el.getAnimations()[0];a.pause();a.currentTime=time;});
         return [getComputedStyle(nodes[0]).backgroundColor,getComputedStyle(nodes[1]).opacity];
        };
        const states=[sample(0),sample(3300)]; nodes.forEach(el=>el.getAnimations()[0].play()); return states;
       });
       assert.deepEqual(cameraStates,[['rgb(36, 37, 34)','1'],['rgb(227, 76, 67)','0']],'Camera changes off/on icon and active color');
      assert.equal(await selection.evaluate(el=>el.getAnimations().length),1);
      const positions=await selection.evaluate(el=>{
       const animation=el.getAnimations()[0];
       animation.pause();
       animation.currentTime=0; const first=getComputedStyle(el).transform;
       animation.currentTime=2400; const second=getComputedStyle(el).transform;
       animation.play(); return [first,second];
      });
       assert.notEqual(positions[0],positions[1],'Selection must switch between alphabets');
       assert(await page.locator('.alphabet-motion .motion-cursor').evaluate(el=>{
        const blur=el.getAnimations().find(a=>a.animationName==='cursor-blur');
        blur.pause(); blur.currentTime=960;
        const active=getComputedStyle(el).filter.includes('blur(0.8px)'); blur.play(); return active;
       }),'Cursor should blur during movement');
       await page.getByRole('button',{name:/Pause animations/}).click();
       await page.locator('.motion-paused').waitFor();
       assert.equal(await selection.evaluate(el=>getComputedStyle(el).animationPlayState),'paused');
       assert.equal(await page.locator('.demo-pose').evaluate(el=>getComputedStyle(el).animationPlayState),'paused');
       await page.getByRole('button',{name:/Resume animations/}).click();
       await page.locator('.how-section:not(.motion-paused)').waitFor();
       await page.locator('.motion-stage').evaluateAll(stages=>stages.forEach(stage=>stage.getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=3300;})));
       await page.locator('#how-it-works').evaluate(el=>el.scrollIntoView());
      await page.screenshot({path:`logs/design/how-it-works-${width}.png`});
      await page.emulateMedia({reducedMotion:'reduce'});
      assert.equal(await selection.evaluate(el=>el.getAnimations().length),0);
       assert(await page.locator('.alphabet-motion .motion-cursor').isHidden());
       assert.equal(await page.locator('.demo-pose').evaluate(el=>el.getAnimations().length),0);
      await page.emulateMedia({reducedMotion:'no-preference'});
     }
    }
    await page.locator('.how-bottom a').click();
    await page.getByRole('textbox',{name:'Text to spell',exact:true}).waitFor();
    assert(new URL(page.url()).pathname==='/text-to-graphics');
    await page.goto(process.env.APP_URL || 'http://localhost:8519');
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
   console.log('PASS: desktop/mobile home, tutorial loops/blur/pause/reduced motion, no live camera, anchors and CTA.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
