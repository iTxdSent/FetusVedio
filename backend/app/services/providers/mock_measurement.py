from typing import Any

from app.schemas.inference import MeasurementResult
from app.services.providers.base import MeasurementProvider

PLANE_METRICS = {
    "BV": {"SVC": 31.0, "IVC": 40.0},
    "AAV": {"AAo": 31.0, "TA": 29.0, "Isthmus": 23.0, "DAo": 32.0},
    "3VT": {"DA": 28.0, "DAo": 30.0},
}


class MockMeasurementProvider(MeasurementProvider):
    def measure(self, frame_bgr: Any, plane: str, mask: Any) -> MeasurementResult:
        metrics = PLANE_METRICS.get(plane, {})
        if mask is None:
            metrics = {}

        return MeasurementResult(
            success=bool(metrics),
            plane=plane,
            metrics=metrics,
            qc={"mask_nonempty": mask is not None, "topology_ok": True, "anatomy_rule_ok": True},
        )
