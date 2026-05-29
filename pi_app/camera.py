"""Camera abstraction with three tiers:
  1. picamera2 — Raspberry Pi camera module (production)
  2. cv2.VideoCapture — USB webcam or laptop camera (development)
  3. Synthetic test pattern — no hardware at all (CI / design)
"""
import io
import logging
import threading
import time

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2  # type: ignore[import]
    _PICAMERA2 = True
except ImportError:
    _PICAMERA2 = False

try:
    import cv2  # type: ignore[import]
    _CV2 = True
except ImportError:
    _CV2 = False


class Camera:
    def __init__(self, width: int = 1280, height: int = 720) -> None:
        self.width = width
        self.height = height
        self._lock = threading.Lock()
        self._frame: bytes | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._picam = None
        self._cap = None  # cv2.VideoCapture

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if _PICAMERA2:
            self._picam = Picamera2()
            config = self._picam.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
            )
            self._picam.configure(config)
            self._picam.start()
            logger.info("picamera2 started (%dx%d)", self.width, self.height)
        elif _CV2:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap = cap
                logger.info("cv2.VideoCapture fallback started")
            else:
                cap.release()
                logger.warning("cv2.VideoCapture(0) failed — using test pattern")
        else:
            logger.warning("No camera library available — using test pattern")

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._picam:
            self._picam.stop()
            self._picam.close()
            self._picam = None
        if self._cap:
            self._cap.release()
            self._cap = None

    # ------------------------------------------------------------------
    # Frame capture loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while self._running:
            try:
                frame = self._capture_frame()
                with self._lock:
                    self._frame = frame
            except Exception:
                logger.exception("Frame capture error")
            time.sleep(0.033)  # ~30 fps

    def _capture_frame(self) -> bytes:
        img = self._capture_image()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return buf.getvalue()

    def _capture_image(self) -> Image.Image:
        if self._picam is not None:
            arr = self._picam.capture_array()
            return Image.fromarray(arr)
        if self._cap is not None:
            ret, frame = self._cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(rgb)
        return self._test_pattern()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_frame(self) -> bytes | None:
        with self._lock:
            return self._frame

    def capture_photo(self, filepath: str) -> None:
        """Save a full-resolution still to *filepath* (JPEG)."""
        if self._picam is not None:
            self._picam.capture_file(filepath)
            return
        elif self._cap is not None:
            ret, frame = self._cap.read()
            if ret:
                cv2.imwrite(filepath, frame)
                return
            # fall through to PIL save
        img = self._test_pattern(add_timestamp=True)
        img.save(filepath, "JPEG", quality=95)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _test_pattern(self, add_timestamp: bool = False) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), (28, 28, 46))
        draw = ImageDraw.Draw(img)
        lines = [
            "PHOTOBOOTH",
            "No Camera Connected",
        ]
        if add_timestamp:
            import datetime
            lines.append(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

        y = self.height // 2 - len(lines) * 14
        for line in lines:
            # Rough centering: default PIL font is 6px wide per char
            x = max(0, self.width // 2 - len(line) * 4)
            draw.text((x, y), line, fill=(180, 180, 220))
            y += 28
        return img


# ------------------------------------------------------------------
# MJPEG generator (Flask streaming response)
# ------------------------------------------------------------------

def mjpeg_generator(camera: Camera):
    """Yield MJPEG boundary frames forever."""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        time.sleep(0.033)
