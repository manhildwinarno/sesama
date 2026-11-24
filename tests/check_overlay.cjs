// node tests/check_overlay.cjs: real component JS, synthetic inference timing.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('local_camera.py', 'utf8').split('    js="""')[1].split('""",')[0];
let now = 0, points = 0;
const ctx = new Proxy({}, {get: (_, key) => key === 'arc' ? () => points++ : () => {}});
const element = () => ({style:{}, setAttribute(){}});
const nodes = Object.fromEntries(['video','canvas','.camera','p','.mirror','.landmarks'].map(k => [k,element()]));
Object.assign(nodes.video, {videoWidth:640, videoHeight:480});
nodes.canvas.getContext = () => ctx;
const root = {querySelector: key => nodes[key]};
const render = vm.runInNewContext(source.replace('export default function', '(function') + ')', {
  performance:{now:() => now}, document:{createElement:element,addEventListener(){},removeEventListener(){}},
  requestAnimationFrame:() => 1, cancelAnimationFrame(){}, clearInterval(){},
});
const data = {mirror:false,show:true,overlay:{stamp:1,age:.1,flip:false,points:[Array.from({length:21}, () => [.5,.5])]}};
render({parentElement:root,data,setStateValue(){}});
function visible(time) {
  now = time; points = 0; root.cameraState.draw(); return points > 0;
}
assert(visible(400), 'Overlay must bridge normal frame/result gap, not blink after 350ms');
assert(visible(800), 'Latest landmarks must remain between delayed results');
assert(!visible(1000), 'Disconnected overlay must expire');
now = 1100;
render({parentElement:root,data:{...data,overlay:{...data.overlay,stamp:2,age:0,points:[]}},setStateValue(){}});
assert(!visible(1100), 'Confirmed no-hand result must clear overlay immediately');
Object.assign(root.cameraState, {waiting:true,sequence:4,lastPost:1000});
render({parentElement:root,data:{...data,ack:3},setStateValue(){}});
assert(root.cameraState.waiting, 'Old acknowledgment must not release pending frame');
render({parentElement:root,data:{...data,ack:4},setStateValue(){}});
assert(!root.cameraState.waiting && root.cameraState.ok, 'Matching acknowledgment must restore connection');
assert(nodes.p.textContent.includes('100 ms'), 'Round-trip timing must be visible');
let first = 0, latest = 0;
render({parentElement:root,data,setStateValue(){},setTriggerValue(){first++;}});
render({parentElement:root,data,setStateValue(){},setTriggerValue(){latest++;}});
root.cameraState.emitFrame({});
assert.equal(first, 0, 'Frame loop must not use stale render callback');
assert.equal(latest, 1, 'Frame loop must use latest trigger callback');
nodes['.empty'] = element();
let stopped = false;
root.cameraState.stream = {getTracks:() => [{stop(){stopped=true;}}]};
render({parentElement:root,data:{...data,mode:'BISINDO'},setStateValue(){}});
assert(stopped && root.cameraState.stream === null, 'Mode change must stop old track even when DOM is reused');
console.log('PASS: landmark hold bridges delayed results, expires on stall, clears on no-hand.');
