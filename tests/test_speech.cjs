const assert = require('node:assert/strict');
const fs = require('node:fs');
let recognition, emitted, cleanup;
const button = {setAttribute() {}, textContent: ''};
const status = {textContent: ''};
global.window = {SpeechRecognition: class {
 constructor() { recognition = this; }
 start() { this.started = true; }
 stop() { this.stopped = true; }
 abort() { this.aborted = true; }
}, addEventListener() {}, removeEventListener() {}};
global.document = {addEventListener() {}, removeEventListener() {}};
const source = fs.readFileSync('assets/speech_input.js', 'utf8').replace('export default function', 'return function');
cleanup = new Function(source)()({parentElement:{querySelector:s=>s==='button'?button:status},setTriggerValue:(key,value)=>{emitted={key,value};}});
button.onclick();
assert(recognition.started);
assert.equal(recognition.lang, 'id-ID');
const result = [{transcript:'halo'}]; result.isFinal = true;
recognition.onresult({results:[result]});
assert.deepEqual(emitted,{key:'transcript',value:'halo'});
assert(recognition.stopped);
recognition.onerror({error:'not-allowed'});
assert(status.textContent.includes('permission denied'));
cleanup();
assert(recognition.aborted);
console.log('PASS: speech start, final transcript, stop, permission error, cleanup');
