import base64
import time
from threading import Lock
from threading import Event, Thread
from typing import Any

import cv2
import numpy as np

from app.schemas.inference import MeasurementResult, SegmentationResult
from app.services.providers.base import ClassifierProvider, MeasurementProvider, SegmentationProvider
from app.services.persistence import AutoCaptureDecider, PersistenceService
from app.services.realtime.frame_cache import LatestFrameCache
from app.services.realtime.session_state import SessionSnapshot, SessionStateStore
from app.services.realtime.video_sources import CaptureCardVideoSource, LocalVideoFileSource, SyntheticVideoSource


class StreamProcessor:
    def __init__(
        self,
        state_store: SessionStateStore,
        cache: LatestFrameCache,
        capture_device_index: int,
        fps: int,
        jpeg_quality: int,
        synthetic_width: int,
        synthetic_height: int,
        classifier_provider: ClassifierProvider,
        segmentation_provider: SegmentationProvider,
        measurement_provider: MeasurementProvider,
        persistence_service: PersistenceService,
        auto_capture_decider: AutoCaptureDecider,
    ) -> None:
        self._state_store = state_store
        self._cache = cache
        self._frame_interval = 1.0 / max(1, fps)
        self._jpeg_quality = jpeg_quality

        self._classifier = classifier_provider
        self._segmenter = segmentation_provider
        self._measurement = measurement_provider
        self._persistence = persistence_service
        self._auto_capture_decider = auto_capture_decider

        self._capture_source = CaptureCardVideoSource(capture_device_index)
        self._local_source: LocalVideoFileSource | None = None
        self._synthetic_source = SyntheticVideoSource(synthetic_width, synthetic_height)

        self._stop_event = Event()
        self._thread: Thread | None = None

        self._last_payload: dict[str, Any] | None = None
        self._latest_raw_frame: Any = None
        self._latest_overlay_frame: Any = None
        self._latest_result_payload: dict[str, Any] | None = None
        self._latest_measurement_id: int | None = None
        self._latest_lock = Lock()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._release_sources()

    def _release_sources(self) -> None:
        self._capture_source.release()
        if self._local_source is not None:
            self._local_source.release()

    def get_latest_payload(self) -> dict[str, Any]:
        cached = self._cache.get()
        if cached is not None:
            return cached
        snapshot = self._state_store.get_snapshot()
        return self._build_idle_payload(snapshot, snapshot.source_state)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            start = time.time()
            try:
                snapshot = self._state_store.get_snapshot()

                if not snapshot.exam_active:
                    payload = self._build_idle_payload(snapshot, snapshot.source_state)
                    self._cache.set(payload)
                    self._last_payload = payload
                elif snapshot.freeze and self._last_payload is not None:
                    payload = dict(self._last_payload)
                    payload["source_state"] = "FROZEN"
                    payload["auto_capture_status"] = snapshot.auto_capture_status
                    self._state_store.set_source_state("FROZEN")
                    self._cache.set(payload)
                else:
                    frame, source_state = self._read_frame(snapshot)
                    payload = self._run_inference(frame, source_state)
                    self._cache.set(payload)
                    self._last_payload = payload
            except Exception:
                snapshot = self._state_store.get_snapshot()
                payload = self._build_idle_payload(snapshot, "PROCESSING_ERROR")
                self._state_store.set_source_state("PROCESSING_ERROR")
                self._cache.set(payload)

            elapsed = time.time() - start
            sleep_sec = self._frame_interval - elapsed
            if sleep_sec > 0:
                time.sleep(sleep_sec)

    def _read_frame(self, snapshot: SessionSnapshot) -> tuple[Any, str]:
        if snapshot.source_mode == "local" and snapshot.local_video_path:
            if self._local_source is None or self._local_source.video_path != snapshot.local_video_path:
                if self._local_source is not None:
                    self._local_source.release()
                self._local_source = LocalVideoFileSource(snapshot.local_video_path)
            ok, frame = self._local_source.read()
            if ok and frame is not None:
                self._state_store.set_source_state("RUNNING_LOCAL")
                return frame, "RUNNING_LOCAL"

        if snapshot.source_mode == "capture":
            ok, frame = self._capture_source.read()
            if ok and frame is not None:
                self._state_store.set_source_state("RUNNING_CAPTURE")
                return frame, "RUNNING_CAPTURE"

        ok, fallback = self._synthetic_source.read()
        source_state = "SOURCE_ERROR" if ok else "NO_SIGNAL"
        self._state_store.set_source_state(source_state)
        if fallback is None:
            fallback = np.zeros((540, 960, 3), dtype=np.uint8)
        return fallback, source_state

    def _run_inference(self, frame: Any, source_state: str) -> dict[str, Any]:
        cls_result = self._classifier.predict(frame)

        if cls_result.plane == "OTHER":
            seg_result = SegmentationResult(success=False, plane="OTHER", mask=None, labels=[])
            measure_result = MeasurementResult(
                success=False,
                plane="OTHER",
                metrics={},
                qc={"mask_nonempty": False, "topology_ok": False, "anatomy_rule_ok": False},
            )
        else:
            seg_result = self._segmenter.predict(frame, cls_result.plane)
            measure_result = self._measurement.measure(frame, cls_result.plane, seg_result.mask)

        frame_index = self._state_store.next_frame_index()
        state = self._state_store.get_snapshot()
        spacing_cm_per_pixel = state.spacing_cm_per_pixel
        metrics_mm = self._convert_metrics_px_to_mm(measure_result.metrics, spacing_cm_per_pixel)
        measurement_success = bool(measure_result.success and metrics_mm)
        qc_pass = bool(measurement_success and measure_result.qc and all(measure_result.qc.values()))
        overlay = self._draw_overlay(
            frame,
            cls_result.plane,
            cls_result.confidence,
            seg_result,
            metrics_mm,
            source_state,
            spacing_cm_per_pixel,
        )

        auto_capture_status = state.auto_capture_status
        measurement_id: int | None = None

        if state.exam_active and state.patient_id is not None and state.session_id is not None:
            if cls_result.plane != "OTHER":
                row = self._persistence.record_measurement(
                    patient_id=state.patient_id,
                    session_id=state.session_id,
                    frame_index=frame_index,
                    plane=cls_result.plane,
                    success=measurement_success,
                    metrics=metrics_mm,
                    qc=measure_result.qc,
                )
                measurement_id = row.id

            should_save, reason = self._auto_capture_decider.evaluate(
                plane=cls_result.plane,
                success=measurement_success,
                metrics=metrics_mm,
            )
            auto_capture_status = reason
            if should_save and measurement_id is not None:
                snap_row = self._persistence.save_snapshot(
                    patient_id=state.patient_id,
                    session_id=state.session_id,
                    measurement_id=measurement_id,
                    frame_index=frame_index,
                    plane=cls_result.plane,
                    trigger_type="auto",
                    raw_frame=frame,
                    overlay_frame=overlay,
                    result_payload={
                        "frame_index": frame_index,
                        "plane": cls_result.plane,
                        "confidence": round(float(cls_result.confidence), 4),
                        "metrics": metrics_mm,
                        "metrics_px": measure_result.metrics,
                        "spacing_cm_per_pixel": spacing_cm_per_pixel,
                        "qc": measure_result.qc,
                        "source_state": source_state,
                    },
                )
                auto_capture_status = f"已自动留图（ID {snap_row.id}）"

            self._state_store.set_auto_capture_status(auto_capture_status)

        payload = {
            "frame_index": frame_index,
            "image_base64": self._encode_jpeg_base64(overlay),
            "plane": cls_result.plane,
            "confidence": round(float(cls_result.confidence), 4),
            "metrics": metrics_mm,
            "metrics_px": measure_result.metrics,
            "qc_pass": qc_pass,
            "source_state": source_state,
            "auto_capture_status": auto_capture_status,
            "spacing_cm_per_pixel": spacing_cm_per_pixel,
            "segmentation": {
                "success": seg_result.success,
                "plane": seg_result.plane,
                "labels": seg_result.labels,
                "mask": seg_result.mask,
            },
            "qc": measure_result.qc,
        }
        with self._latest_lock:
            self._latest_raw_frame = frame.copy()
            self._latest_overlay_frame = overlay.copy()
            self._latest_result_payload = dict(payload)
            self._latest_measurement_id = measurement_id
        return payload

    def _build_idle_payload(self, snapshot: SessionSnapshot, source_state: str) -> dict[str, Any]:
        _, frame = self._synthetic_source.read()
        if frame is None:
            frame = np.zeros((540, 960, 3), dtype=np.uint8)
        cv2.putText(frame, "检查未开始", (40, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (220, 220, 220), 2)
        return {
            "frame_index": snapshot.frame_index,
            "image_base64": self._encode_jpeg_base64(frame),
            "plane": "OTHER",
            "confidence": 0.0,
            "metrics": {},
            "qc_pass": False,
            "source_state": source_state,
            "auto_capture_status": snapshot.auto_capture_status,
            "spacing_cm_per_pixel": snapshot.spacing_cm_per_pixel,
            "segmentation": {"success": False, "plane": "OTHER", "labels": [], "mask": None},
            "qc": {"mask_nonempty": False, "topology_ok": False, "anatomy_rule_ok": False},
        }

    def _draw_overlay(
        self,
        frame: Any,
        plane: str,
        confidence: float,
        seg_result: SegmentationResult,
        metrics_mm: dict[str, float],
        source_state: str,
        spacing_cm_per_pixel: float | None,
    ) -> Any:
        canvas = frame.copy()

        if seg_result.success and isinstance(seg_result.mask, dict):
            self._draw_mock_mask(canvas, seg_result.mask)

        cv2.putText(canvas, f"Plane: {plane}", (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 220, 80), 2)
        cv2.putText(canvas, f"Confidence: {confidence:.2f}", (16, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
        cv2.putText(canvas, f"Source: {source_state}", (16, 86), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
        spacing_text = "--" if spacing_cm_per_pixel is None else f"{spacing_cm_per_pixel:.4f} cm/px"
        cv2.putText(canvas, f"Spacing: {spacing_text}", (16, 114), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (220, 220, 220), 2)

        y = 142
        for key, value in metrics_mm.items():
            cv2.putText(canvas, f"{key}: {value:.2f} mm", (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.66, (255, 220, 80), 2)
            y += 28

        return canvas

    def _draw_mock_mask(self, frame: Any, mask: dict[str, Any]) -> None:
        mask_type = mask.get("type")
        if mask_type == "circles":
            for item in mask.get("items", []):
                center = (int(item.get("cx", 0)), int(item.get("cy", 0)))
                radius = int(item.get("r", 0))
                cv2.circle(frame, center, radius, (80, 255, 80), 2)
        elif mask_type == "polygon":
            points = mask.get("points", [])
            if len(points) >= 3:
                pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (80, 255, 80), 2)

    def _encode_jpeg_base64(self, frame: Any) -> str:
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self._jpeg_quality])
        if not ok:
            return ""
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def manual_save_snapshot(self):
        state = self._state_store.get_snapshot()
        if state.patient_id is None or state.session_id is None:
            self._state_store.set_auto_capture_status("未绑定患者或会话，无法手动保存")
            return None

        with self._latest_lock:
            has_latest = (
                self._latest_raw_frame is not None
                and self._latest_overlay_frame is not None
                and self._latest_result_payload is not None
            )
            if has_latest:
                raw_frame = self._latest_raw_frame.copy()
                overlay_frame = self._latest_overlay_frame.copy()
                result_payload = dict(self._latest_result_payload)
                measurement_id = self._latest_measurement_id
            else:
                fallback_payload = self.get_latest_payload()
                fallback_frame = self._decode_jpeg_base64(fallback_payload.get("image_base64", ""))
                if fallback_frame is None:
                    self._state_store.set_auto_capture_status("当前无可保存帧")
                    return None
                raw_frame = fallback_frame
                overlay_frame = fallback_frame
                result_payload = dict(fallback_payload)
                measurement_id = None

        row = self._persistence.save_snapshot(
            patient_id=state.patient_id,
            session_id=state.session_id,
            measurement_id=measurement_id,
            frame_index=result_payload.get("frame_index", 0),
            plane=result_payload.get("plane", "OTHER"),
            trigger_type="manual",
            raw_frame=raw_frame,
            overlay_frame=overlay_frame,
            result_payload=result_payload,
        )
        self._state_store.set_auto_capture_status(f"手动保存成功（ID {row.id}）")
        return row

    def reset_auto_capture(self) -> None:
        self._auto_capture_decider.reset()

    def _decode_jpeg_base64(self, image_base64: str):
        if not image_base64:
            return None
        try:
            buf = base64.b64decode(image_base64)
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def _convert_metrics_px_to_mm(
        self,
        metrics_px: dict[str, float],
        spacing_cm_per_pixel: float | None,
    ) -> dict[str, float]:
        if spacing_cm_per_pixel is None or spacing_cm_per_pixel <= 0:
            return {}
        factor = spacing_cm_per_pixel * 10.0
        return {k: round(float(v) * factor, 4) for k, v in metrics_px.items()}
