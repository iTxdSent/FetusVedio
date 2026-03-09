from pydantic import BaseModel, Field


class SessionStateResponse(BaseModel):
    exam_active: bool
    freeze: bool
    source_mode: str
    source_state: str
    local_video_path: str | None
    frame_index: int
    patient_id: int | None
    session_id: int | None
    auto_capture_status: str
    user_id: int | None
    spacing_cm_per_pixel: float | None
    spacing_confirmed: bool


class SwitchLocalVideoRequest(BaseModel):
    video_path: str = Field(..., description="本地视频文件路径")


class StartExamRequest(BaseModel):
    patient_id: int | None = None


class SpacingSetRequest(BaseModel):
    spacing_cm_per_pixel: float = Field(..., gt=0)
