import cv2
import numpy as np
from typing import Optional
import threading
from queue import Queue, Empty
import time
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class HighPerformanceCameraService:
    """
    Multi-threaded camera service for high FPS capture.
    
    Architecture:
    - Capture thread: grabs frames at native camera FPS
    - Main thread: reads latest frame (never blocked by processing)
    """

    def __init__(self, camera_id: str = "default", source=0):
        self.camera_id = camera_id
        self.source = source
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.target_fps = 30
        self.resolution = (1280, 720)

        # Threaded capture
        self._capture_thread: Optional[threading.Thread] = None
        self._frame_queue: Queue = Queue(maxsize=2)
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Stats
        self.actual_fps = 0.0
        self._fps_counter = []
        self._frames_captured = 0

    def _capture_loop(self):
        """Runs in separate thread - captures frames as fast as possible"""
        while not self._stop_event.is_set():
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.01)
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            with self._frame_lock:
                self._latest_frame = frame_rgb

            # Track FPS
            self._frames_captured += 1
            now = time.time()
            self._fps_counter.append(now)
            self._fps_counter = [t for t in self._fps_counter if now - t < 1.0]
            self.actual_fps = len(self._fps_counter)

            # Small sleep to prevent CPU spinning at 100%
            time.sleep(0.001)

    async def start(self) -> bool:
        """Start threaded camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.source}")
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            self._stop_event.clear()
            self._capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True
            )
            self._capture_thread.start()
            self.is_running = True
            logger.info(f"Camera {self.camera_id} started (threaded)")
            return True

        except Exception as e:
            logger.error(f"Camera start error: {e}")
            return False

    async def stop(self):
        """Stop camera capture"""
        self._stop_event.set()
        self.is_running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info(f"Camera {self.camera_id} stopped")

    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest captured frame (non-blocking)"""
        with self._frame_lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
        return None

    async def get_frame_for_detection(self, max_size: int = 640) -> Optional[np.ndarray]:
        """Get frame resized for fast detection"""
        frame = await self.get_frame()
        if frame is None:
            return None

        h, w = frame.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            frame = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

        return frame

    def get_status(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "is_running": self.is_running,
            "actual_fps": self.actual_fps,
            "source": self.source,
            "resolution": self.resolution,
        }
