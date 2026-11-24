// NODE_PATH=<Playwright location> APP_URL=http://localhost:8519 node tests/check_home.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
async function waitForAnchor(page,id) {
 await page.waitForFunction(id=>{
  const main=document.querySelector('[data-testid="stMain"]');
  const target=document.getElementById(id);
  const top=target.getBoundingClientRect().top-main.getBoundingClientRect().top+main.scrollTop-parseFloat(getComputedStyle(target).scrollMarginTop||0);
  return Math.abs(main.scrollTop-Math.max(0,Math.min(top,main.scrollHeight-main.clientHeight)))<2;
 },id);
}
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
     assert.equal(await page.locator('.landing-placeholder').count(),0);
     assert.equal(await page.locator('#benefits .benefits-list > li').count(),3);
     assert.equal(await page.locator('#benefits').getByText('Coming soon.',{exact:true}).count(),0);
     await page.getByRole('contentinfo',{name:'Site footer'}).waitFor();
     assert.equal(await page.locator('.landing-footer a[href*="instagram"]').count(),0);
     assert.equal(await page.locator('.footer-links a').count(),6);
    assert.equal(await page.locator('#benchmark table').count(),2);
    assert.equal(await page.locator('#benchmark tbody tr').count(),6);
    assert.deepEqual(await page.locator('.benchmark-selected td').allTextContents(),['95.92%','95.84%','95.95%','95.92%']);
    assert(await page.getByTestId('stMainBlockContainer').evaluate(el=>el.scrollHeight<=el.clientHeight+1),'White panel must contain all sections');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Home overflows viewport');
    const main=page.getByTestId('stMain');
    assert(await main.evaluate(el=>getComputedStyle(el).scrollbarGutter==='stable'));
    const mainBox=await main.boundingBox();
    const margin=width<768?8:16;
    const cardBox=await page.getByTestId('stMainBlockContainer').boundingBox();
    const area=await main.evaluate(el=>({width:el.clientWidth,background:getComputedStyle(el).backgroundColor}));
     assert.equal(area.background,'rgba(0, 0, 0, 0)','Scrollbar container must show gradient, not white');
     assert.equal(await main.evaluate(el=>getComputedStyle(el).scrollBehavior),'smooth');
     const brand=page.locator('.landing-nav .landing-brand');
     await brand.hover();
     assert.deepEqual(await brand.evaluate(el=>{const s=getComputedStyle(el);return [s.backgroundColor,s.transform,s.transitionDuration];}),['rgba(0, 0, 0, 0)','none','0s']);
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
      await waitForAnchor(page,anchor);
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
        assert.equal(await page.getByRole('button',{name:/Pause animations|Resume animations/}).count(),0);
        assert.equal(await page.locator('.motion-label, .motion-example').count(),0);
        const transcript=await page.locator('.text-motion').evaluate(stage=>{
         const sample=time=>{
          stage.getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=time;});
          return ['.demo-letter-h','.demo-letter-i','.demo-space'].map((selector,i)=>{
           const style=getComputedStyle(stage.querySelector(selector));return i===2?style.width:style.opacity;
          });
         };
         return [sample(0),sample(1800),sample(3300),sample(5100)];
        });
        assert.deepEqual(transcript,[['0','0','0px'],['1','1','0px'],['1','1','18px'],['1','1','0px']],'Transcript shows HI, adds space, then deletes space');
       await page.locator('.motion-stage').evaluateAll(stages=>stages.forEach(stage=>stage.getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=3300;})));
       await page.locator('#how-it-works').evaluate(el=>el.scrollIntoView());
      await page.screenshot({path:`logs/design/how-it-works-${width}.png`});
       await page.emulateMedia({reducedMotion:'reduce'});
       assert.equal(await main.evaluate(el=>getComputedStyle(el).scrollBehavior),'auto');
      assert.equal(await selection.evaluate(el=>el.getAnimations().length),0);
       assert(await page.locator('.alphabet-motion .motion-cursor').isHidden());
        assert.equal(await page.locator('.demo-pose').evaluate(el=>el.getAnimations().length),0);
        assert.equal(await page.locator('.text-motion').evaluate(el=>el.getAnimations({subtree:true}).length),0);
      await page.emulateMedia({reducedMotion:'no-preference'});
     }
     if(anchor==='benefits') {
      const heading=await page.locator('.benefits-heading').boundingBox();
      const list=await page.locator('.benefits-list').boundingBox();
      assert(width<768 ? list.y>=heading.y+heading.height : list.x>=heading.x+heading.width,'Benefits stack only on mobile');
      assert(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth<=el.clientWidth),'Benefits must not overflow horizontally');
      await page.screenshot({path:`logs/design/benefits-${width}.png`});
     }
     if(anchor==='faq') {
      const faq=page.locator('.st-key-landing-faq');
      const entries=faq.locator('details');
      assert.equal(await entries.count(),6);
      assert.equal(await faq.locator('details[open]').count(),0,'FAQ starts collapsed');
      for(const entry of await entries.all()) {
       const summary=entry.locator('summary');
       await summary.focus();
       await summary.press('Enter');
       await page.waitForFunction(el=>el.open,await entry.elementHandle());
       assert(await entry.evaluate(el=>el.open),'Keyboard opens FAQ');
       assert(await entry.getByTestId('stExpanderDetails').isVisible());
       await summary.press('Space');
       await page.waitForFunction(el=>!el.open,await entry.elementHandle());
       assert(!(await entry.evaluate(el=>el.open)),'Keyboard closes FAQ');
      }
      await entries.nth(4).locator('summary').click();
      assert(await faq.getByText(/Frames are sent to the app server/).isVisible());
      await entries.nth(5).locator('summary').click();
      assert(await faq.getByText(/sends your transcript to Google/).isVisible());
      assert(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth<=el.clientWidth),'FAQ must not overflow');
      await page.locator('#faq').evaluate(el=>el.scrollIntoView());
      await faq.screenshot({path:`logs/design/faq-${width}.png`,animations:'disabled'});
      await entries.nth(4).locator('summary').click();
      await entries.nth(5).locator('summary').click();
     }
     if(anchor==='benchmark') {
      const tables=await page.locator('.benchmark-dataset').all();
      const boxes=await Promise.all(tables.map(table=>table.boundingBox()));
      assert(width<768 ? boxes[1].y>boxes[0].y : Math.abs(boxes[1].y-boxes[0].y)<1);
      assert.equal(await page.locator('.benchmark-method, .benchmark-caveat').count(),0);
      assert.equal(await page.locator('.evaluation-link').getAttribute('href'),'/model-evaluation');
      await page.locator('#benchmark').evaluate(el=>el.scrollIntoView());
      await page.screenshot({path:`logs/design/benchmark-${width}.png`});
     }
     }
     await page.locator('.landing-footer').evaluate(el=>el.scrollIntoView({behavior:'instant',block:'end'}));
     const footerColumns=await page.locator('.footer-columns > *').evaluateAll(es=>es.map(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y};}));
     assert(width<768 ? footerColumns[1].y>footerColumns[0].y : Math.abs(footerColumns[1].y-footerColumns[0].y)<1,'Footer columns stack on mobile');
     assert(await main.evaluate(el=>el.scrollWidth<=el.clientWidth),'Footer must not overflow');
     await page.locator('.landing-footer').screenshot({path:`logs/design/footer-${width}.png`});
     await page.locator('.footer-links a[href="#how-it-works"]').click();
     await waitForAnchor(page,'how-it-works');
     await page.locator('.st-key-landing-faq details').nth(3).locator('summary').click();
     await page.locator('.st-key-landing-faq').getByRole('link',{name:/Model evaluation/}).click();
    await page.getByRole('heading',{name:'Why we chose SVM.',exact:true}).waitFor();
    assert.equal(new URL(page.url()).pathname,'/model-evaluation');
    await page.getByTestId('stSidebar').waitFor({state:'hidden'});
    await page.getByTestId('stVegaLiteChart').nth(1).waitFor();
    assert((await page.getByTestId('stVegaLiteChart').count())>=2);
    await page.getByRole('radio',{name:'Accuracy',exact:true}).click();
    await page.getByTestId('stVegaLiteChart').first().waitFor();
    assert.equal(await page.locator('video').count(),0);
    assert(await page.getByText('SVM leads weighted F1 by 4.00 percentage points',{exact:false}).isVisible());
    assert(await page.getByText('SVM leads weighted F1 by 2.78 percentage points',{exact:false}).isVisible());
    assert.equal(await page.locator('img').count(),0,'Evaluation uses charts, not report images');
    assert.equal(await page.getByRole('switch').count(),0,'Heatmap has no extra toggles');
    await page.getByText('Read the limits',{exact:true}).waitFor();
    await page.getByText('Supporting analysis',{exact:true}).click();
    await page.getByRole('heading',{name:'Samples per letter',exact:true}).waitFor();
    assert.equal(await page.getByTestId('stVegaLiteChart').count(),6);
    for(const element of await page.locator('[data-testid="stVegaLiteChart"], [data-testid="stDataFrame"]').all()) {
     await element.scrollIntoViewIfNeeded();
     await element.hover();
     const isTable=await element.getAttribute('data-testid')==='stDataFrame';
     const toolbar=(isTable?element:element.locator('..')).getByTestId('stElementToolbar');
     await toolbar.getByRole('button',{name:'Fullscreen',exact:true}).waitFor();
     const buttons=toolbar.locator('button:visible');
     assert.deepEqual(await buttons.evaluateAll(es=>es.map(e=>e.getAttribute('aria-label'))),[
      isTable?'Download as CSV':'Download as PNG','Fullscreen'
     ]);
     const toolbarBox=await toolbar.boundingBox();
     const content=isTable?element.getByTestId('stDataFrameResizable'):element;
     const contentBox=await content.boundingBox();
     assert(toolbarBox.y+toolbarBox.height<=contentBox.y+1,'Toolbar must not overlap content');
     assert.equal(await toolbar.evaluate(el=>getComputedStyle(el).backgroundColor),'rgba(0, 0, 0, 0)');
    }
    const heatmap=page.getByTestId('stVegaLiteChart').nth(2).locator('..');
    assert.equal(await heatmap.getByRole('graphics-symbol',{name:/Count.*legend/i}).count(),0);
    // Force CSV fallback instead of Chromium's native save dialog in headless tests.
    await page.evaluate(()=>{window.showSaveFilePicker=async()=>{throw new Error('Use download fallback');};});
    const download=page.waitForEvent('download');
    await page.getByTestId('stDataFrame').first().getByRole('button',{name:'Download as CSV',exact:true}).click();
    assert((await download).suggestedFilename().endsWith('.csv'));
    await heatmap.getByRole('button',{name:'Fullscreen',exact:true}).click();
    await page.getByRole('button',{name:'Close fullscreen',exact:true}).click();
    const back=page.locator('.st-key-evaluation-back');
    assert.equal(await back.evaluate(el=>getComputedStyle(el).marginTop),'48px');
    await page.getByRole('heading',{name:'Inside the SIBI evaluation',exact:true}).evaluate(el=>el.scrollIntoView());
    await page.screenshot({path:`logs/design/confusion-${width}.png`});
    assert(await page.getByTestId('stMain').evaluate(el=>el.scrollWidth<=el.clientWidth),'Evaluation must not overflow horizontally');
    await page.getByTestId('stMain').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:`logs/design/evaluation-${width}.png`});
    await page.getByRole('link',{name:/Back to home/}).first().click();
    await page.getByRole('heading',{name:'Every letter. A little closer.'}).waitFor();
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
   console.log('PASS: desktop/mobile home, three tutorial loops, blur/reduced motion, clean labels, no live camera, anchors and CTA.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
