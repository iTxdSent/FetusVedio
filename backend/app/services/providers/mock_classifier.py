from typing import Any

from app.schemas.inference import ClassificationResult
from app.services.providers.base import ClassifierProvider

PLANES = ["OTHER", "BV", "AAV", "3VT"]


class MockClassifierProvider(ClassifierProvider):
    def __init__(self) -> None:
        self._frame_index = 0

    def predict(self, frame_bgr: Any) -> ClassificationResult:
        plane = PLANES[(self._frame_index // 60) % len(PLANES)]
        class_id = PLANES.index(plane)
        confidence = 0.65 if plane == "OTHER" else 0.92
        self._frame_index += 1
        return ClassificationResult(plane=plane, class_id=class_id, confidence=confidence)
