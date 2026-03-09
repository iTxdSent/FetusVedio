from typing import Any

from app.schemas.inference import SegmentationResult
from app.services.providers.base import SegmentationProvider


class MockSegmentationProvider(SegmentationProvider):
    def __init__(self) -> None:
        self._call_index = 0

    def predict(self, frame_bgr: Any, plane: str) -> SegmentationResult:
        if plane == "OTHER":
            return SegmentationResult(success=False, plane=plane, mask=None, labels=[])

        self._call_index += 1
        if self._call_index % 40 == 0:
            return SegmentationResult(success=False, plane=plane, mask=None, labels=[])

        h, w = frame_bgr.shape[:2]
        if plane == "BV":
            mask = {
                "type": "circles",
                "items": [
                    {"cx": int(w * 0.38), "cy": int(h * 0.48), "r": int(min(h, w) * 0.09)},
                    {"cx": int(w * 0.57), "cy": int(h * 0.5), "r": int(min(h, w) * 0.1)},
                ],
            }
            labels = [0, 1]
        elif plane == "AAV":
            mask = {
                "type": "polygon",
                "points": [
                    [int(w * 0.28), int(h * 0.58)],
                    [int(w * 0.42), int(h * 0.44)],
                    [int(w * 0.56), int(h * 0.38)],
                    [int(w * 0.7), int(h * 0.44)],
                    [int(w * 0.62), int(h * 0.62)],
                    [int(w * 0.4), int(h * 0.68)],
                ],
            }
            labels = [0, 1, 2]
        else:  # 3VT
            mask = {
                "type": "circles",
                "items": [
                    {"cx": int(w * 0.42), "cy": int(h * 0.5), "r": int(min(h, w) * 0.1)},
                    {"cx": int(w * 0.6), "cy": int(h * 0.49), "r": int(min(h, w) * 0.085)},
                ],
            }
            labels = [0, 1]

        return SegmentationResult(success=True, plane=plane, mask=mask, labels=labels)
