from app.core.config import settings
from app.services.providers.registry import build_provider_bundle
from app.services.persistence import AutoCaptureDecider, PersistenceService
from app.services.realtime.frame_cache import LatestFrameCache
from app.services.realtime.session_state import SessionStateStore
from app.services.realtime.stream_processor import StreamProcessor

session_state_store = SessionStateStore()
latest_frame_cache = LatestFrameCache()
provider_bundle = build_provider_bundle(settings.model_provider_backend)
persistence_service = PersistenceService()
auto_capture_decider = AutoCaptureDecider(
    consecutive_frames=settings.auto_capture_consecutive_frames,
    cooldown_sec=settings.auto_capture_cooldown_sec,
)

stream_processor = StreamProcessor(
    state_store=session_state_store,
    cache=latest_frame_cache,
    capture_device_index=settings.capture_device_index,
    fps=settings.stream_fps,
    jpeg_quality=settings.jpeg_quality,
    synthetic_width=settings.synthetic_width,
    synthetic_height=settings.synthetic_height,
    classifier_provider=provider_bundle.classifier,
    segmentation_provider=provider_bundle.segmentation,
    measurement_provider=provider_bundle.measurement,
    persistence_service=persistence_service,
    auto_capture_decider=auto_capture_decider,
)
