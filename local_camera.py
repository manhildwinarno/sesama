"""Preview browser lokal; WebRTC hanya mengirim video untuk inferensi."""
import asyncio
from aiortc.mediastreams import MediaStreamError
from concurrent.futures import TimeoutError

import streamlit as st
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration
from streamlit_webrtc.eventloop import get_global_event_loop


class CameraConnection:
    def __init__(self, engine, loop=None):
        self.engine = engine
        self.loop = loop if loop is not None else get_global_event_loop()
        self.pc = None
        self.offer_id = None
        self.answer = None
        self.tasks = set()
        self.error = ""

    async def _close(self):
        if self.pc:
            await self.pc.close()
            self.pc = None

    async def _answer(self, offer):
        await self._close()
        pc = self.pc = RTCPeerConnection(RTCConfiguration(iceServers=[]))

        @pc.on("connectionstatechange")
        async def state_changed():
            if pc.connectionState == "failed":
                await pc.close()

        @pc.on("track")
        def track_received(track):
            async def consume():
                try:
                    while track.readyState == "live":
                        frame = await track.recv()
                        self.engine.submit(frame)
                except MediaStreamError:
                    pass
                except Exception as exc:
                    self.error = f"Penerimaan video berhenti: {type(exc).__name__}: {exc}"
                    if pc.connectionState not in ("closed", "failed"):
                        await pc.close()
            task = asyncio.create_task(consume())
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type="offer"))
        await pc.setLocalDescription(await pc.createAnswer())
        return {"id": offer["id"], "sdp": pc.localDescription.sdp, "type": "answer"}

    def answer_offer(self, offer):
        if (not isinstance(offer, dict) or not isinstance(offer.get("id"), str)
                or len(offer["id"]) > 100 or not isinstance(offer.get("sdp"), str)
                or len(offer["sdp"]) > 100000):
            raise ValueError("Offer kamera tidak valid")
        if offer.get("id") != self.offer_id:
            future = asyncio.run_coroutine_threadsafe(self._answer(offer), self.loop)
            try:
                self.answer = future.result(timeout=15)
            except TimeoutError:
                future.cancel()
                raise RuntimeError("Koneksi kamera melewati batas waktu; tekan STOP lalu START.")
            self.offer_id = offer.get("id")
        return self.answer

    def close(self):
        asyncio.run_coroutine_threadsafe(self._close(), self.loop).result(timeout=5)


camera = st.components.v2.component(
    "local_camera",
    html="""<div class="view"><video autoplay muted playsinline></video><canvas></canvas></div>
<button type="button">START</button><p role="status">Kamera belum aktif.</p>""",
    css="""
.view {position:relative; aspect-ratio:16/9; background:#232C29; border-radius:10px; overflow:hidden;}
video,canvas {position:absolute; width:100%; height:100%; object-fit:contain;}
canvas {pointer-events:none;}
button {margin-top:10px; padding:10px 20px; background:#19766D; color:white; border:0; border-radius:10px; cursor:pointer;}
p {font:14px sans-serif; color:var(--st-text-color);}
""",
    js="""
export default function({parentElement, data, setStateValue}) {
 const root=parentElement, video=root.querySelector('video'), canvas=root.querySelector('canvas');
 const button=root.querySelector('button'), status=root.querySelector('p');
 let s=root.cameraState;
 if(!s) {
  s=root.cameraState={pc:null,stream:null,busy:false,token:0,answer:null,overlay:null};
  s.stop=()=>{
   s.token++; if(s.pc) s.pc.close(); s.pc=null;
   if(s.stream) s.stream.getTracks().forEach(t=>t.stop()); s.stream=null;
   video.srcObject=null; button.textContent='START'; s.busy=false; button.disabled=false;
    status.textContent='Kamera berhenti.'; setStateValue('playing',false); setStateValue('stopped',s.token);
  };
  button.onclick=async()=>{
   if(s.stream || s.busy) {s.stop(); return;}
   s.busy=true; button.disabled=true; const token=++s.token;
   status.textContent='Izinkan akses kamera di browser…';
   try {
    const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720},frameRate:{ideal:30,max:30}},audio:false});
    if(token!==s.token) {stream.getTracks().forEach(t=>t.stop());return;}
    s.stream=stream; video.srcObject=stream; await video.play();
    const pc=s.pc=new RTCPeerConnection({iceServers:[]});
    stream.getVideoTracks().forEach(t=>pc.addTrack(t,stream));
    pc.getTransceivers().forEach(t=>t.direction='sendonly');
    pc.onconnectionstatechange=()=>{
     if(token!==s.token) return;
      const active=pc.connectionState==='connected';
      if(active || pc.connectionState==='failed' || pc.connectionState==='closed') setStateValue('playing',active);
     status.textContent=active?'Preview lokal · inferensi terhubung':`Preview lokal · koneksi ${pc.connectionState}`;
    };
    await pc.setLocalDescription(await pc.createOffer());
    if(pc.iceGatheringState!=='complete') await new Promise((resolve,reject)=>{
     const timer=setTimeout(()=>reject(Error('ICE timeout')),10000);
     pc.addEventListener('icegatheringstatechange',()=>{if(pc.iceGatheringState==='complete'){clearTimeout(timer);resolve();}});
    });
    if(token!==s.token) return;
    const id=crypto.randomUUID(); s.offerId=id; s.answer=null;
    setStateValue('offer',{id,sdp:pc.localDescription.sdp});
    button.textContent='STOP'; button.disabled=false; s.busy=false;
   } catch(e) {if(token===s.token){s.stop();status.textContent=`Kamera gagal: ${e.message}`;}}
  };
  s.draw=()=>{
   canvas.width=video.videoWidth||1280;canvas.height=video.videoHeight||720;
   const ctx=canvas.getContext('2d'), o=s.overlay;
   if(s.show && o && performance.now()-s.received<250) {
    ctx.strokeStyle='#DDEAE5';ctx.fillStyle='#63CEB5';ctx.lineWidth=2;
    for(const hand of o.points) {
     const points=hand.map(([x,y])=>[(o.flip?1-x:x)*canvas.width,y*canvas.height]);
     for(const [a,b] of [[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]]) {
      ctx.beginPath();ctx.moveTo(...points[a]);ctx.lineTo(...points[b]);ctx.stroke();
     }
     for(const p of points){ctx.beginPath();ctx.arc(...p,3,0,2*Math.PI);ctx.fill();}
    }
   }
   s.raf=requestAnimationFrame(s.draw);
  }; s.draw();
 }
 s.show=data.show; video.style.transform=canvas.style.transform=data.mirror?'scaleX(-1)':'none';
 if(data.overlay && data.overlay.stamp!==s.stamp) {s.stamp=data.overlay.stamp;s.overlay=data.overlay;s.received=performance.now();}
 if(data.answer && s.pc && data.answer.id===s.offerId && s.answer!==data.answer.id) {
  s.answer=data.answer.id;s.pc.setRemoteDescription(data.answer).catch(e=>{status.textContent=`Koneksi gagal: ${e.message}`;});
 }
 return ()=>{cancelAnimationFrame(s.raf);s.token++;if(s.pc)s.pc.close();if(s.stream)s.stream.getTracks().forEach(t=>t.stop());delete root.cameraState;};
}
""",
)
