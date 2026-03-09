from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
from sqlalchemy import desc, select

from app.core.config import settings
from app.db.models import ExamSession, Measurement, Patient, Snapshot, User
from app.db.session import SessionLocal

REQUIRED_METRICS = {
    "BV": ["SVC", "IVC"],
    "AAV": ["AAo", "TA", "Isthmus", "DAo"],
    "3VT": ["DA", "DAo"],
}


class AutoCaptureDecider:
    def __init__(self, consecutive_frames: int, cooldown_sec: int) -> None:
        self._consecutive_frames = max(1, consecutive_frames)
        self._cooldown_sec = max(0, cooldown_sec)
        self._last_plane: str | None = None
        self._consecutive_ok = 0
        self._last_saved_ts_by_plane: dict[str, float] = {}

    def reset(self) -> None:
        self._last_plane = None
        self._consecutive_ok = 0
        self._last_saved_ts_by_plane = {}

    def _metrics_complete(self, plane: str, metrics: dict[str, float]) -> bool:
        required = REQUIRED_METRICS.get(plane, [])
        return all(key in metrics and metrics[key] is not None for key in required)

    def evaluate(self, plane: str, success: bool, metrics: dict[str, float]) -> tuple[bool, str]:
        if plane == "OTHER":
            self._last_plane = None
            self._consecutive_ok = 0
            return False, "切面为 OTHER，不留图"

        if not success:
            self._last_plane = None
            self._consecutive_ok = 0
            return False, "测量未成功，不留图"

        if not self._metrics_complete(plane, metrics):
            self._last_plane = None
            self._consecutive_ok = 0
            return False, "测量字段不完整，不留图"

        if self._last_plane == plane:
            self._consecutive_ok += 1
        else:
            self._last_plane = plane
            self._consecutive_ok = 1

        if self._consecutive_ok < self._consecutive_frames:
            return False, f"连续帧不足（{self._consecutive_ok}/{self._consecutive_frames}）"

        now_ts = time.time()
        last_ts = self._last_saved_ts_by_plane.get(plane, 0.0)
        if now_ts - last_ts < self._cooldown_sec:
            remain = int(self._cooldown_sec - (now_ts - last_ts))
            return False, f"同切面冷却中（约{max(0, remain)}秒）"

        self._last_saved_ts_by_plane[plane] = now_ts
        self._consecutive_ok = 0
        self._last_plane = plane
        return True, "已自动留图"


class PersistenceService:
    def __init__(self) -> None:
        self._snapshot_root_dir = Path(settings.snapshot_root_dir).expanduser().resolve()

    def create_patient(self, user_id: int, name: str, patient_code: str, gestation_week: str) -> Patient:
        with SessionLocal() as db:
            patient = Patient(user_id=user_id, name=name, patient_code=patient_code, gestation_week=gestation_week)
            db.add(patient)
            db.commit()
            db.refresh(patient)
            return patient

    def list_patients(self, user_id: int) -> list[Patient]:
        with SessionLocal() as db:
            rows = (
                db.execute(select(Patient).where(Patient.user_id == user_id).order_by(desc(Patient.id))).scalars().all()
            )
            return list(rows)

    def get_patient(self, user_id: int, patient_id: int) -> Patient | None:
        with SessionLocal() as db:
            return (
                db.execute(
                    select(Patient).where(Patient.id == patient_id).where(Patient.user_id == user_id).limit(1)
                )
                .scalars()
                .first()
            )

    def start_session(self, patient_id: int) -> ExamSession:
        with SessionLocal() as db:
            session = ExamSession(patient_id=patient_id, status="ACTIVE")
            db.add(session)
            db.commit()
            db.refresh(session)
            return session

    def end_session(self, session_id: int) -> None:
        with SessionLocal() as db:
            row = db.get(ExamSession, session_id)
            if row is None:
                return
            row.status = "ENDED"
            row.ended_at = datetime.utcnow()
            db.add(row)
            db.commit()

    def record_measurement(
        self,
        patient_id: int,
        session_id: int,
        frame_index: int,
        plane: str,
        success: bool,
        metrics: dict[str, float],
        qc: dict[str, bool],
    ) -> Measurement:
        with SessionLocal() as db:
            row = Measurement(
                patient_id=patient_id,
                session_id=session_id,
                frame_index=frame_index,
                plane=plane,
                success=success,
                metrics=metrics,
                qc=qc,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def save_snapshot(
        self,
        patient_id: int,
        session_id: int,
        measurement_id: int | None,
        frame_index: int,
        plane: str,
        trigger_type: str,
        raw_frame: Any,
        overlay_frame: Any,
        result_payload: dict[str, Any],
    ) -> Snapshot:
        patient_dir = self._snapshot_root_dir / f"patient_{patient_id}"
        patient_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        prefix = f"{stamp}_{trigger_type}_{plane}"

        raw_abs = patient_dir / f"{prefix}_raw.jpg"
        overlay_abs = patient_dir / f"{prefix}_overlay.jpg"
        result_abs = patient_dir / f"{prefix}_result.json"

        cv2.imwrite(str(raw_abs), raw_frame)
        cv2.imwrite(str(overlay_abs), overlay_frame)
        result_abs.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        raw_rel = raw_abs.relative_to(self._snapshot_root_dir.parent).as_posix()
        overlay_rel = overlay_abs.relative_to(self._snapshot_root_dir.parent).as_posix()
        result_rel = result_abs.relative_to(self._snapshot_root_dir.parent).as_posix()

        with SessionLocal() as db:
            row = Snapshot(
                patient_id=patient_id,
                session_id=session_id,
                measurement_id=measurement_id,
                frame_index=frame_index,
                plane=plane,
                trigger_type=trigger_type,
                raw_path=raw_rel,
                overlay_path=overlay_rel,
                result_json_path=result_rel,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def list_snapshots(self, user_id: int, patient_id: int, limit: int = 200) -> list[Snapshot]:
        patient = self.get_patient(user_id=user_id, patient_id=patient_id)
        if patient is None:
            return []
        with SessionLocal() as db:
            rows = db.execute(
                select(Snapshot)
                .where(Snapshot.patient_id == patient_id)
                .order_by(desc(Snapshot.id))
                .limit(limit)
            ).scalars().all()
            return list(rows)

    def get_latest_snapshot(self, user_id: int, patient_id: int) -> Snapshot | None:
        patient = self.get_patient(user_id=user_id, patient_id=patient_id)
        if patient is None:
            return None
        with SessionLocal() as db:
            return db.execute(
                select(Snapshot)
                .where(Snapshot.patient_id == patient_id)
                .order_by(desc(Snapshot.id))
                .limit(1)
            ).scalars().first()

    def get_user(self, user_id: int) -> User | None:
        with SessionLocal() as db:
            return db.get(User, user_id)
