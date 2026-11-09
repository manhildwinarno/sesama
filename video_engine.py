"""Worker inferensi satu slot frame terbaru; frame masuk dari POST kamera lokal."""
from collections import deque
from threading import Condition, Lock, Thread
from time import monotonic

import cv2
import pandas as pd

CONNECTIONS = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7),
               (7, 8), (5, 9), (9, 10), (10, 11), (11, 12), (9, 13),
               (13, 14), (14, 15), (15, 16), (13, 17), (0, 17),
               (17, 18), (18, 19), (19, 20))


def draw_overlay(image, landmarks, flip):
    height, width = image.shape[:2]
    for hand in landmarks:
        points = [(round((1-x if flip else x)*(width-1)), round(y*(height-1))) for x, y in hand]
        for a, b in CONNECTIONS:
            cv2.line(image, points[a], points[b], (220, 220, 220), 1, cv2.LINE_AA)
        for point in points:
            cv2.circle(image, point, 2, (70, 210, 100), -1, cv2.LINE_AA)


class VideoEngine:
    def __init__(self, artifacts, hands_factory):
        self.artifacts = artifacts
        self.hands_factory = hands_factory
        self.condition = Condition()
        self.lock = Lock()
        self.pending = None
        self.running = True
        self.config = (False, False, True, 65, 0.5)
        self.show_landmarks = False
        self.overlay = ((), 0.0, False)
        self.events = deque()
        self.result = {"candidate": "", "confidence": 0.0, "error": "", "ms": 0.0}
        self.times = deque(maxlen=60)
        self.last_frame = 0.0
        self.thread = Thread(target=self._work, daemon=True)
        self.thread.start()

    def configure(self, flip, reverse, mirror, threshold, hold, show_landmarks=False):
        with self.lock:
            self.config = (flip, reverse, mirror, threshold, hold)
            self.show_landmarks = show_landmarks

    def submit(self, image):
        height, width = image.shape[:2]
        scale = min(1, 640 / width, 480 / height)
        if scale < 1:
            image = cv2.resize(image, (round(width * scale), round(height * scale)))
        with self.lock:
            self.times.append(monotonic())
            self.last_frame = monotonic()
        with self.condition:
            self.pending = image
            self.condition.notify()

    def overlay_snapshot(self):
        with self.lock:
            points, stamp, flip = self.overlay
            return {"points": points if monotonic() - stamp <= 1.0 else (),
                    "stamp": stamp, "flip": flip}

    def snapshot(self):
        with self.lock:
            result = dict(self.result)
            result["fps"] = ((len(self.times)-1)/(self.times[-1]-self.times[0])
                             if len(self.times) > 1 and self.times[-1] > self.times[0] else 0)
            result["active"] = monotonic() - self.last_frame < 1.0
            result["ago"] = monotonic() - self.last_frame if self.last_frame else None
            events = list(self.events)
            self.events.clear()
            return result, events

    def close(self):
        with self.condition:
            self.running = False
            self.pending = None
            self.condition.notify_all()
        # MediaPipe ditutup worker yang memilikinya.
        self.thread.join(timeout=5)

    def _work(self):
        hands = None
        try:
            hands = self.hands_factory()
            model, scaler, encoder = self.artifacts
            last, since, latched = "", 0.0, False
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.pending is not None or not self.running)
                    if not self.running:
                        return
                    image, self.pending = self.pending, None
                    captured = monotonic()
                with self.lock:
                    config = self.config
                flip, reverse, _, threshold, hold = config
                started = monotonic()
                if flip:
                    image = cv2.flip(image, 1)
                detected = list(hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)).multi_hand_landmarks or [])
                candidate, confidence = "", 0.0
                needed = int(scaler.n_features_in_) // 63
                if 0 < len(detected) <= needed:
                    if reverse:
                        detected.reverse()
                    features = [v for hand in detected for lm in hand.landmark for v in (lm.x, lm.y, lm.z)]
                    # BISINDO CSV: satu tangan pada h0; seluruh h1 nol sebelum scaler.
                    features.extend([0.0] * (63 * needed - len(features)))
                    values = pd.DataFrame([features], columns=scaler.feature_names_in_) if hasattr(scaler, "feature_names_in_") else [features]
                    values = scaler.transform(values)
                    pred = model.predict(values)[0]
                    confidence = float(model.predict_proba(values)[0][list(model.classes_).index(pred)]) * 100
                    candidate = str(encoder.inverse_transform([pred])[0])
                char = candidate if confidence >= threshold else ""
                now = monotonic()
                if char != last:
                    last, since, latched = char, now, False
                with self.lock:
                    # Jangan publikasikan prediksi dari orientasi/pengaturan lama.
                    if config != self.config:
                        last, latched = "", False
                        continue
                    self.overlay = (tuple(tuple((lm.x, lm.y) for lm in hand.landmark)
                                          for hand in detected), captured, flip)
                    if char and not latched and now-since >= hold:
                        self.events.append(char)
                        latched = True
                    self.result = dict(candidate=candidate, confidence=confidence, error="",
                                       ms=(now-started)*1000, count=len(detected))
        except Exception as exc:
            with self.lock:
                self.result["error"] = str(exc)
        finally:
            if hands is not None:
                hands.close()
