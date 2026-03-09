from copy import deepcopy
from threading import Lock
from typing import Any


class LatestFrameCache:
    def __init__(self) -> None:
        self._lock = Lock()
        self._payload: dict[str, Any] | None = None

    def set(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._payload = deepcopy(payload)

    def get(self) -> dict[str, Any] | None:
        with self._lock:
            if self._payload is None:
                return None
            return deepcopy(self._payload)
