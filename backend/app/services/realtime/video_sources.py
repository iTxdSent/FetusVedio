import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np


class BaseVideoSource(ABC):
    @abstractmethod
    def read(self) -> tuple[bool, np.ndarray | None]:
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        raise NotImplementedError


class CaptureCardVideoSource(BaseVideoSource):
    def __init__(self, device_index: int) -> None:
        self._device_index = device_index
        self._cap: cv2.VideoCapture | None = None
        self._last_open_attempt = 0.0
        self._open_retry_interval_sec = 2.0

    def _ensure_opened(self) -> bool:
        if self._cap is not None and self._cap.isOpened():
            return True

        now = time.time()
        if now - self._last_open_attempt < self._open_retry_interval_sec:
            return False
        self._last_open_attempt = now

        # 避免在 macOS 无权限场景反复触发摄像头权限弹窗。
        os.environ.setdefault("OPENCV_AVFOUNDATION_SKIP_AUTH", "1")
        self._cap = cv2.VideoCapture(self._device_index)
        if not self._cap.isOpened():
            self._cap.release()
            self._cap = None
            return False
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self._ensure_opened():
            return False, None
        ok, frame = self._cap.read()
        return ok, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class LocalVideoFileSource(BaseVideoSource):
    def __init__(self, video_path: str) -> None:
        self._video_path = str(Path(video_path).expanduser().resolve())
        self._cap: cv2.VideoCapture | None = None

    @property
    def video_path(self) -> str:
        return self._video_path

    def _ensure_opened(self) -> bool:
        if self._cap is not None and self._cap.isOpened():
            return True
        if not Path(self._video_path).exists():
            return False
        self._cap = cv2.VideoCapture(self._video_path)
        return self._cap.isOpened()

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self._ensure_opened():
            return False, None
        ok, frame = self._cap.read()
        if ok:
            return True, frame
        # 到末尾自动回放，保证演示链路持续。
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = self._cap.read()
        return ok, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class SyntheticVideoSource(BaseVideoSource):
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self._counter = 0

    def read(self) -> tuple[bool, np.ndarray | None]:
        self._counter += 1
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)
        frame[:, :, 0] = 35
        frame[:, :, 1] = 45
        frame[:, :, 2] = 60

        offset = (self._counter * 8) % max(1, self._width - 180)
        cv2.rectangle(frame, (offset, 100), (offset + 160, 200), (70, 130, 220), -1)
        cv2.putText(frame, "DEMO SOURCE", (30, self._height - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (220, 220, 220), 2)
        return True, frame

    def release(self) -> None:
        return
