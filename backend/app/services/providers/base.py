from abc import ABC, abstractmethod
from typing import Any

from app.schemas.inference import ClassificationResult, MeasurementResult, SegmentationResult


class ClassifierProvider(ABC):
    @abstractmethod
    def predict(self, frame_bgr: Any) -> ClassificationResult:
        raise NotImplementedError


class SegmentationProvider(ABC):
    @abstractmethod
    def predict(self, frame_bgr: Any, plane: str) -> SegmentationResult:
        raise NotImplementedError


class MeasurementProvider(ABC):
    @abstractmethod
    def measure(self, frame_bgr: Any, plane: str, mask: Any) -> MeasurementResult:
        raise NotImplementedError
