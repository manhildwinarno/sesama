"""Preview kamera lokal di browser; frame dikirim ke Python lewat HTTP loopback."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread

import cv2
import numpy as np
import streamlit as st


class FrameServer:
    def __init__(self):
        self.engines = {}
        self.lock = Lock()
        server = self

        class Handler(BaseHTTPRequestHandler):
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
                try:
                    length = int(self.headers.get("Content-Length", 0))
                except ValueError:
                    length = 0
                if not 0 < length <= 4_000_000:
                    self._reply(413, close=True)
                    return
                image = cv2.imdecode(np.frombuffer(self.rfile.read(length), np.uint8),
                                     cv2.IMREAD_COLOR)
                if image is None:
                    self._reply(400)
                    return
                engine.submit(image)
                self._reply(204)

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
    html="""<div class="view"><video autoplay muted playsinline></video><canvas></canvas></div>
<button type="button">START</button><p role="status">Kamera belum aktif.</p>""",
    css="""
.view {position:relative; aspect-ratio:16/9; background:#232C29; border-radius:10px; overflow:hidden; margin-bottom:10px;}
video,canvas {position:absolute; width:100%; height:100%; object-fit:contain;}
canvas {pointer-events:none;}
button {padding:10px 20px; background:#19766D; color:white; border:0; border-radius:10px; cursor:pointer;}
button:disabled {opacity:.6; cursor:wait;}
p {font:14px sans-serif; color:var(--st-text-color);}
""",
    js="""
export default function({parentElement, data}) {
 const root=parentElement, video=root.querySelector('video'), canvas=root.querySelector('canvas');
 const button=root.querySelector('button'), status=root.querySelector('p');
 let s=root.cameraState;
 if(!s) {
  s=root.cameraState={stream:null,busy:false,timer:null,raf:null,inflight:false,ok:false,overlay:null,show:false,frameCanvas:document.createElement('canvas')};
  const post=async()=>{
   if(!s.stream || s.inflight || document.hidden) return;
   if(!video.videoWidth) return;
   const frame=s.frameCanvas, scale=Math.min(1,640/video.videoWidth,480/video.videoHeight);
   frame.width=Math.round(video.videoWidth*scale); frame.height=Math.round(video.videoHeight*scale);
   const ctx=frame.getContext('2d');
   ctx.drawImage(video,0,0,frame.width,frame.height);
   s.inflight=true;
   try {
    const blob=await new Promise(r=>frame.toBlob(r,'image/jpeg',0.75));
    if(!blob || !s.stream) return;
    const response=await fetch(data.url,{method:'POST',headers:{'Content-Type':'image/jpeg','X-Frame-Token':data.token},body:blob});
    if(!response.ok) throw Error(`HTTP ${response.status}`);
    if(!s.ok) {s.ok=true;status.textContent='Preview lokal · inferensi menerima frame.';}
   } catch(e) {
    if(s.ok) {s.ok=false;status.textContent=`Kamera aktif · inferensi terputus (${e.message}).`;}
   } finally {s.inflight=false;}
  };
  s.stop=()=>{
   if(s.timer) clearInterval(s.timer); s.timer=null;
   if(s.raf) cancelAnimationFrame(s.raf); s.raf=null;
   if(s.stream) s.stream.getTracks().forEach(t=>t.stop()); s.stream=null;
   video.srcObject=null; button.textContent='START'; button.disabled=false; s.busy=false; s.ok=false;
   status.textContent='Kamera berhenti.';
  };
  button.onclick=async()=>{
   if(s.stream) {s.stop(); return;}
   s.busy=true; button.disabled=true; status.textContent='Izinkan akses kamera di browser…';
   try {
    const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30,max:30}},audio:false});
    if(!s.busy) {stream.getTracks().forEach(t=>t.stop());return;}
    s.stream=stream; video.srcObject=stream; await video.play();
    status.textContent='Preview lokal · mengirim frame…';
    button.textContent='STOP'; button.disabled=false; s.busy=false;
    s.timer=setInterval(post,100);
   } catch(e) {
    s.busy=false; button.disabled=false; status.textContent=`Kamera gagal: ${e.message}`;
   }
  };
  s.draw=()=>{
   const w=video.videoWidth, h=video.videoHeight;
   if(w && h) {
    if(canvas.width!==w || canvas.height!==h) {canvas.width=w;canvas.height=h;}
    const ctx=canvas.getContext('2d'); ctx.clearRect(0,0,w,h);
    const o=s.overlay;
    if(s.show && o && performance.now()-s.received<600) {
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
 s.show=data.show;
 video.style.transform=canvas.style.transform=data.mirror?'scaleX(-1)':'none';
 if(data.overlay && data.overlay.stamp!==s.stamp) {s.stamp=data.overlay.stamp;s.overlay=data.overlay;s.received=performance.now();}
 return ()=>{s.busy=false;s.stop();delete root.cameraState;};
}
""",
)
