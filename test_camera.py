"""python test_camera.py: WebRTC nyata tanpa webcam/browser."""
import asyncio
from threading import Event

import av
import numpy as np
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription, VideoStreamTrack
from local_camera import CameraConnection


class Frames(VideoStreamTrack):
    async def recv(self):
        pts, base = await self.next_timestamp()
        frame = av.VideoFrame.from_ndarray(np.zeros((360, 640, 3), dtype=np.uint8), format="bgr24")
        frame.pts, frame.time_base = pts, base
        return frame


async def check():
    received = Event()
    count = 0
    class Engine:
        def submit(self, frame):
            nonlocal count
            count += 1
            if count >= 90:
                received.set()
    connection = CameraConnection(Engine(), loop=asyncio.get_running_loop())
    pc = RTCPeerConnection(RTCConfiguration(iceServers=[]))
    try:
        pc.addTrack(Frames())
        pc.getTransceivers()[0].direction = "sendonly"
        await pc.setLocalDescription(await pc.createOffer())
        answer = await asyncio.to_thread(connection.answer_offer, {"id": "test", "sdp": pc.localDescription.sdp})
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"], type="answer"))
        assert await asyncio.to_thread(received.wait, 15), connection.error or "Tidak menerima frame"
        print(f"OK: {count} frame WebRTC nyata diterima engine, bukan hanya koneksi tersambung.")
    finally:
        await pc.close()
        await asyncio.to_thread(connection.close)


if __name__ == "__main__":
    asyncio.run(check())
