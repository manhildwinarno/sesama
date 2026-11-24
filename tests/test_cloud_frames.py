"""python tests/test_cloud_frames.py: bounded cloud JPEG decoder."""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from local_camera import decode_frame

def jpeg(height, width):
    ok, raw = cv2.imencode('.jpg', np.zeros((height, width, 3), np.uint8))
    assert ok
    return base64.b64encode(raw).decode('ascii')

assert decode_frame(jpeg(480, 640)).shape == (480, 640, 3)
for payload in (None, {}, '!', 'A' * 600_001, base64.b64encode(b'not jpeg').decode(), jpeg(481, 640)):
    try:
        decode_frame(payload)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid browser frame accepted')
print('PASS: valid cloud JPEG accepted; malformed, oversized and excessive dimensions rejected.')
