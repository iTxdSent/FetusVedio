from dataclasses import dataclass
from threading import Lock
from typing import Literal

SourceMode = Literal["capture", "local"]


@dataclass(frozen=True)
class SessionSnapshot:
    exam_active: bool
    freeze: bool
    source_mode: SourceMode
    source_state: str
    local_video_path: str | None
    frame_index: int
    patient_id: int | None
    session_id: int | None
    auto_capture_status: str
    user_id: int | None
    spacing_cm_per_pixel: float | None
    spacing_confirmed: bool


class SessionStateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._exam_active = False
        self._freeze = False
        self._source_mode: SourceMode = "capture"
        self._source_state = "IDLE"
        self._local_video_path: str | None = None
        self._frame_index = 0
        self._patient_id: int | None = None
        self._session_id: int | None = None
        self._auto_capture_status = "等待检查开始"
        self._user_id: int | None = None
        self._spacing_cm_per_pixel: float | None = None
        self._spacing_confirmed = False

    def _snapshot_unlocked(self) -> SessionSnapshot:
        return SessionSnapshot(
            exam_active=self._exam_active,
            freeze=self._freeze,
            source_mode=self._source_mode,
            source_state=self._source_state,
            local_video_path=self._local_video_path,
            frame_index=self._frame_index,
            patient_id=self._patient_id,
            session_id=self._session_id,
            auto_capture_status=self._auto_capture_status,
            user_id=self._user_id,
            spacing_cm_per_pixel=self._spacing_cm_per_pixel,
            spacing_confirmed=self._spacing_confirmed,
        )

    def get_snapshot(self) -> SessionSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def start_exam(self) -> SessionSnapshot:
        with self._lock:
            self._exam_active = True
            self._freeze = False
            self._frame_index = 0
            self._source_state = "RUNNING_LOCAL" if self._source_mode == "local" else "RUNNING_CAPTURE"
            self._auto_capture_status = "检查开始，等待留图条件"
            return self._snapshot_unlocked()

    def end_exam(self) -> SessionSnapshot:
        with self._lock:
            self._exam_active = False
            self._freeze = False
            self._source_state = "ENDED"
            self._auto_capture_status = "检查已结束"
            return self._snapshot_unlocked()

    def freeze_exam(self) -> SessionSnapshot:
        with self._lock:
            self._freeze = True
            self._source_state = "FROZEN"
            return self._snapshot_unlocked()

    def unfreeze_exam(self) -> SessionSnapshot:
        with self._lock:
            self._freeze = False
            if self._exam_active:
                self._source_state = "RUNNING_LOCAL" if self._source_mode == "local" else "RUNNING_CAPTURE"
            return self._snapshot_unlocked()

    def switch_local_video(self, video_path: str) -> SessionSnapshot:
        with self._lock:
            self._source_mode = "local"
            self._local_video_path = video_path
            if self._exam_active and not self._freeze:
                self._source_state = "RUNNING_LOCAL"
            return self._snapshot_unlocked()

    def resume_capture(self) -> SessionSnapshot:
        with self._lock:
            self._source_mode = "capture"
            self._local_video_path = None
            if self._exam_active and not self._freeze:
                self._source_state = "RUNNING_CAPTURE"
            return self._snapshot_unlocked()

    def set_source_state(self, source_state: str) -> SessionSnapshot:
        with self._lock:
            self._source_state = source_state
            return self._snapshot_unlocked()

    def next_frame_index(self) -> int:
        with self._lock:
            self._frame_index += 1
            return self._frame_index

    def bind_patient(self, patient_id: int) -> SessionSnapshot:
        with self._lock:
            self._patient_id = patient_id
            return self._snapshot_unlocked()

    def bind_user(self, user_id: int) -> SessionSnapshot:
        with self._lock:
            if self._user_id is not None and self._user_id != user_id:
                self._patient_id = None
                self._session_id = None
                self._exam_active = False
                self._freeze = False
                self._frame_index = 0
                self._source_mode = "capture"
                self._local_video_path = None
                self._source_state = "IDLE"
                self._spacing_cm_per_pixel = None
                self._spacing_confirmed = False
                self._auto_capture_status = "用户已切换，请先确认比例尺"
            self._user_id = user_id
            return self._snapshot_unlocked()

    def bind_session(self, session_id: int | None) -> SessionSnapshot:
        with self._lock:
            self._session_id = session_id
            return self._snapshot_unlocked()

    def clear_session(self) -> SessionSnapshot:
        with self._lock:
            self._session_id = None
            return self._snapshot_unlocked()

    def set_auto_capture_status(self, status: str) -> SessionSnapshot:
        with self._lock:
            self._auto_capture_status = status
            return self._snapshot_unlocked()

    def set_spacing(self, spacing_cm_per_pixel: float) -> SessionSnapshot:
        with self._lock:
            self._spacing_cm_per_pixel = spacing_cm_per_pixel
            self._spacing_confirmed = True
            return self._snapshot_unlocked()
