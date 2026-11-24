"""Browser preview and bounded Streamlit frames; legacy loopback retained for tests."""
import secrets
import json
import base64
import binascii
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

import cv2
import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError


def decode_frame(payload):
    """Validate bounded browser JPEG before passing pixels to inference."""
    if not isinstance(payload, str) or len(payload) > 600_000:
        raise ValueError("Frame exceeds size limit")
    try:
        raw = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid frame encoding") from exc
    if not raw.startswith(b"\xff\xd8"):
        raise ValueError("Expected JPEG frame")
    try:
        with Image.open(io.BytesIO(raw)) as header:
            if header.format != "JPEG" or not (1 <= header.width <= 640 and 1 <= header.height <= 480):
                raise ValueError("Invalid frame dimensions")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid JPEG frame") from exc
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if image is None or not (1 <= image.shape[0] <= 480 and 1 <= image.shape[1] <= 640):
        raise ValueError("Invalid frame dimensions")
    return image


class FrameServer:
    def __init__(self):
        self.engines = {}
        self.lock = Lock()
        server = self

        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                self.connection.settimeout(5)

            def _cors(self):
                origin = self.headers.get("Origin", "")
                if origin.startswith(("http://localhost:", "http://127.0.0.1:")):
                    self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Frame-Token")
                self.send_header("Access-Control-Allow-Private-Network", "true")

            def _reply(self, code, body=b"", close=False):
                self.send_response(code)
                self._cors()
                self.send_header("Content-Length", str(len(body)))
                if close:
                    self.close_connection = True
                    self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self._reply(204)

            def do_POST(self):
                if self.path != "/frame":
                    self._reply(404, close=True)
                    return
                try:
                    length = int(self.headers.get("Content-Length", 0))
                except ValueError:
                    length = 0
                if not 0 < length <= 4_000_000:
                    self._reply(413, close=True)
                    return
                body = self.rfile.read(length)
                origin = self.headers.get("Origin", "")
                if origin and not origin.startswith(("http://localhost:", "http://127.0.0.1:")):
                    self._reply(403, close=True)
                    return
                token = self.headers.get("X-Frame-Token", "")
                with server.lock:
                    engine = server.engines.get(token)
                if engine is None:
                    self._reply(403, close=True)
                    return
                image = cv2.imdecode(np.frombuffer(body, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    self._reply(400)
                    return
                engine.submit(image)
                overlay = engine.overlay_snapshot() if hasattr(engine, "overlay_snapshot") else None
                self._reply(200, json.dumps({"overlay": overlay}).encode())

            def log_message(self, format, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/frame"
        Thread(target=self.httpd.serve_forever, daemon=True).start()

    def register(self, token, engine):
        with self.lock:
            self.engines[token] = engine

    def unregister(self, token):
        with self.lock:
            self.engines.pop(token, None)


_server = None
_server_lock = Lock()


def get_frame_server():
    global _server
    with _server_lock:
        if _server is None:
            _server = FrameServer()
        return _server


def new_token():
    return secrets.token_urlsafe(18)


camera = st.components.v2.component(
    "local_camera",
    html="""<div class="view"><div class="empty"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="12" height="12" rx="3"/><path d="m15 10 6-3v10l-6-3M3 3l18 18"/></svg><strong>Camera off</strong></div><video autoplay muted playsinline></video><canvas></canvas></div>
<div class="dock"><button class="mirror" type="button" aria-label="Mirror preview" aria-pressed="true" title="Mirror preview"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v18M3 7l5-3v16l-5-3zM21 7l-5-3v16l5-3z"/></svg></button><button class="camera" type="button" aria-label="START" aria-pressed="false" title="Turn camera on"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="12" height="12" rx="3"/><path d="m15 10 6-3v10l-6-3"/></svg></button><button class="landmarks" type="button" aria-label="Show hand landmarks" aria-pressed="false" title="Show hand landmarks"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 18 3-7 4 4 4-9 3 12M5 18h14"/><circle cx="8" cy="11" r="2"/><circle cx="16" cy="6" r="2"/></svg></button></div><p role="status">Allow camera access to begin.</p>""",
    css="""
.view {position:relative; aspect-ratio:16/9; background:#292b28; border-radius:24px; overflow:hidden; margin-bottom:14px;}
video,canvas {position:absolute; width:100%; height:100%; object-fit:contain;}
canvas {pointer-events:none;}
.empty {position:absolute; inset:0; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:14px; color:#f4f5ef; font:14px var(--st-font,sans-serif);}
.empty svg {width:42px; height:42px; stroke:#dce2d5; fill:none; stroke-width:1.4;}
.empty strong {font-size:20px; font-weight:500;}
.empty span {color:#c3c8bc;}
.label {position:absolute; left:24px; bottom:22px; color:white; font:12px var(--st-font,sans-serif); background:#0005; padding:7px 12px; border-radius:99px;}
.dock {display:flex; align-items:center; justify-content:center; gap:12px; width:fit-content; margin:0 auto; border-radius:99px; background:#111; padding:8px; color:#fff; font:13px var(--st-font,sans-serif);}
button {display:grid; place-items:center; width:52px; height:52px; background:#383a36; color:white; border:0; border-radius:50%; cursor:pointer; transition:background-color .18s ease, color .18s ease, transform .18s ease, box-shadow .18s ease;}
button svg {width:24px; height:24px; stroke:currentColor; fill:none; stroke-width:1.7;}
button.camera[aria-pressed="true"] {background:#e34c43;}
button:not(.camera)[aria-pressed="true"] {background:#edf1e4; color:#222;}
@media(hover:hover) {
 button:not(:disabled):hover {background:#4b4e47; transform:translateY(-2px); box-shadow:0 4px 10px #0004;}
 button.camera[aria-pressed="true"]:hover {background:#f15b52;}
 button:not(.camera)[aria-pressed="true"]:hover {background:#dce6d0;}
}
button:not(:disabled):active {transform:scale(.95); box-shadow:none;}
button:focus-visible {outline:3px solid #6b7555; outline-offset:3px;}
button:disabled {opacity:.6; cursor:wait;}
@media(prefers-reduced-motion:reduce) {button {transition:none;} button:not(:disabled):hover, button:not(:disabled):active {transform:none;}}
p {font:12px var(--st-font,sans-serif); color:var(--st-text-color); text-align:center;}
@media(max-width:600px) {.view {border-radius:20px;} button {width:44px;height:44px;}}
""",
    js="""
export default function({parentElement, data, setStateValue, setTriggerValue}) {
 const root=parentElement, video=root.querySelector('video'), canvas=root.querySelector('canvas');
 const button=root.querySelector('.camera'), status=root.querySelector('p');
 let s=root.cameraState;
 if(!s) {
  s=root.cameraState={stream:null,busy:false,timer:null,raf:null,inflight:false,ok:false,overlay:null,show:false,frameCanvas:document.createElement('canvas'),controller:null,lastPost:0,data:data};
   const post=async()=>{
    if(!s.stream || document.hidden) return;
    if(s.data.transport==='streamlit' && s.waiting) {
     if(performance.now()-s.lastPost>15000) status.textContent='Connection stalled. Turn camera off and on to retry.';
     return;
    }
   if(s.inflight) {
    if(performance.now()-s.lastPost<3500) return;
    if(s.controller) s.controller.abort(); s.inflight=false;
   }
   if(!video.videoWidth) return;
   const frame=s.frameCanvas, scale=Math.min(1,640/video.videoWidth,480/video.videoHeight);
   frame.width=Math.round(video.videoWidth*scale); frame.height=Math.round(video.videoHeight*scale);
   const ctx=frame.getContext('2d');
   ctx.drawImage(video,0,0,frame.width,frame.height);
   s.inflight=true; s.lastPost=performance.now();
   const controller=s.controller=new AbortController();
   const timer=setTimeout(()=>controller.abort(),2500);
   try {
    const blob=await new Promise(r=>frame.toBlob(r,'image/jpeg',0.75));
    if(!blob || !s.stream || s.controller!==controller) return;
     const d=s.data||data;
     if(d.transport==='streamlit') {
      const reader=new FileReader();
      const encoded=await new Promise((resolve,reject)=>{reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(blob);});
      s.waiting=true; s.sequence=(s.sequence||0)+1;
      setTriggerValue('frame',{jpeg:encoded,sequence:s.sequence});
      return;
     }
    const response=await fetch(d.url,{method:'POST',headers:{'Content-Type':'image/jpeg','X-Frame-Token':d.token},body:blob,signal:controller.signal});
    if(!response.ok) throw Error(`HTTP ${response.status}`);
    const payload=await response.json();
    if(s.controller===controller && payload.overlay) {
     s.overlay=payload.overlay;s.received=performance.now();
    }
    if(s.controller===controller && !s.ok) {s.ok=true;status.textContent='Camera on';}
   } catch(e) {
    if(s.stream && s.controller===controller) {
     s.ok=false;
     status.textContent=`Inference disconnected (${e.name==='AbortError'?'timeout':e.message}). Retrying…`;
    }
   } finally {clearTimeout(timer);if(s.controller===controller){s.controller=null;s.inflight=false;}}
  };
  s.stop=()=>{
    if(s.timer) clearInterval(s.timer); s.timer=null; s.waiting=false;
   if(s.controller) s.controller.abort(); s.controller=null; s.inflight=false;
   if(s.raf) cancelAnimationFrame(s.raf); s.raf=null;
   if(s.stream) s.stream.getTracks().forEach(t=>t.stop()); s.stream=null;
    video.srcObject=null; button.setAttribute('aria-label','START'); button.setAttribute('aria-pressed','false'); button.title='Turn camera on'; root.querySelector('.empty').style.display='flex'; button.disabled=false; s.busy=false; s.ok=false;
    status.textContent='Camera off';
  };
  button.onclick=async()=>{
   if(s.stream) {s.stop(); return;}
    s.busy=true; button.disabled=true; status.textContent='Allow camera access…';
   try {
    const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30,max:30}},audio:false});
    if(!s.busy) {stream.getTracks().forEach(t=>t.stop());return;}
    s.stream=stream; video.srcObject=stream; await video.play();
    root.querySelector('.view').style.aspectRatio=`${video.videoWidth}/${video.videoHeight}`;
    status.textContent='Camera on';
    button.setAttribute('aria-label','STOP'); button.setAttribute('aria-pressed','true'); button.title='Turn camera off'; root.querySelector('.empty').style.display='none'; button.disabled=false; s.busy=false;
    s.timer=setInterval(post,s.data.transport==='streamlit'?200:100);
    if(s.raf===null) s.draw();
   } catch(e) {
    s.busy=false; button.disabled=false; status.textContent=`Camera failed: ${e.message}`;
   }
  };
  s.draw=()=>{
   const w=video.videoWidth, h=video.videoHeight;
   if(w && h) {
    if(canvas.width!==w || canvas.height!==h) {canvas.width=w;canvas.height=h;}
    const ctx=canvas.getContext('2d'); ctx.clearRect(0,0,w,h);
    const o=s.overlay;
     // ponytail: hold latest real result for 1s; faster tracking needs lower transport/inference latency.
     if(s.show && o && performance.now()-s.received<1000) {
     ctx.strokeStyle='#DDEAE5';ctx.fillStyle='#63CEB5';ctx.lineWidth=2;
     for(const hand of o.points) {
      const points=hand.map(([x,y])=>[(o.flip?1-x:x)*w,y*h]);
      for(const [a,b] of [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]]) {
       ctx.beginPath();ctx.moveTo(...points[a]);ctx.lineTo(...points[b]);ctx.stroke();
      }
      for(const p of points){ctx.beginPath();ctx.arc(...p,3,0,2*Math.PI);ctx.fill();}
     }
    }
   }
   s.raf=requestAnimationFrame(s.draw);
  };
  s.draw();
 }
 if(data.ack===s.sequence) {s.waiting=false;}
  root.querySelector('.mirror').onclick=()=>{
   const next=!s.data.mirror; s.data={...s.data,mirror:next};
   root.querySelector('.mirror').setAttribute('aria-pressed',String(next));
   video.style.transform=canvas.style.transform=next?'scaleX(-1)':'none';
   setStateValue('mirror',next);
  };
  root.querySelector('.landmarks').onclick=()=>{
   const next=!s.data.show; s.data={...s.data,show:next}; s.show=next;
   root.querySelector('.landmarks').setAttribute('aria-pressed',String(next));
   setStateValue('show',next);
  };
 root.querySelector('.mirror').setAttribute('aria-pressed',String(data.mirror));
 root.querySelector('.landmarks').setAttribute('aria-pressed',String(data.show));
 s.data=data; s.show=data.show;
 video.style.transform=canvas.style.transform=data.mirror?'scaleX(-1)':'none';
  if(data.overlay && data.overlay.stamp!==s.stamp) {s.stamp=data.overlay.stamp;s.overlay=data.overlay;s.received=performance.now()-(data.overlay.age||0)*1000;}
 return ()=>{s.busy=false;s.stop();delete root.cameraState;};
}
""",
)
