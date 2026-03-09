from typing import Any

from pydantic import BaseModel


class ClassificationResult(BaseModel):
    plane: str
    class_id: int
    confidence: float


class SegmentationResult(BaseModel):
    success: bool
    plane: str
    mask: Any
    labels: list[int]


class MeasurementResult(BaseModel):
    success: bool
    plane: str
    metrics: dict[str, float]
    qc: dict[str, bool]
