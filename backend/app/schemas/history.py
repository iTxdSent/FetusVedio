from datetime import datetime

from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    id: int
    patient_id: int
    session_id: int
    frame_index: int
    plane: str
    trigger_type: str
    overlay_url: str
    raw_url: str
    result_json_url: str
    created_at: datetime
