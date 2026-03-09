from dataclasses import dataclass

from app.services.providers.base import ClassifierProvider, MeasurementProvider, SegmentationProvider
from app.services.providers.mock_classifier import MockClassifierProvider
from app.services.providers.mock_measurement import MockMeasurementProvider
from app.services.providers.mock_segmentation import MockSegmentationProvider


@dataclass(frozen=True)
class ProviderBundle:
    classifier: ClassifierProvider
    segmentation: SegmentationProvider
    measurement: MeasurementProvider


def build_provider_bundle(provider_backend: str) -> ProviderBundle:
    backend = provider_backend.lower().strip()

    if backend == "mock":
        return ProviderBundle(
            classifier=MockClassifierProvider(),
            segmentation=MockSegmentationProvider(),
            measurement=MockMeasurementProvider(),
        )

    raise ValueError(f"不支持的 Provider 后端: {provider_backend}")
