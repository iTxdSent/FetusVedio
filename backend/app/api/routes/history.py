from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.schemas.history import SnapshotResponse
from app.services.auth_service import AuthUser
from app.services.persistence import PersistenceService

router = APIRouter(prefix="/history")
service = PersistenceService()


def _to_snapshot_response(row) -> SnapshotResponse:
    return SnapshotResponse(
        id=row.id,
        patient_id=row.patient_id,
        session_id=row.session_id,
        frame_index=row.frame_index,
        plane=row.plane,
        trigger_type=row.trigger_type,
        overlay_url=f"/media/{row.overlay_path}",
        raw_url=f"/media/{row.raw_path}",
        result_json_url=f"/media/{row.result_json_path}",
        created_at=row.created_at,
    )


@router.get("/patients/{patient_id}/snapshots", response_model=list[SnapshotResponse])
def list_snapshots(patient_id: int, limit: int = 200, current_user: AuthUser = Depends(get_current_user)) -> list[SnapshotResponse]:
    rows = service.list_snapshots(user_id=current_user.id, patient_id=patient_id, limit=limit)
    return [_to_snapshot_response(row) for row in rows]


@router.get("/patients/{patient_id}/latest-snapshot", response_model=SnapshotResponse | None)
def latest_snapshot(patient_id: int, current_user: AuthUser = Depends(get_current_user)) -> SnapshotResponse | None:
    row = service.get_latest_snapshot(user_id=current_user.id, patient_id=patient_id)
    if row is None:
        return None
    return _to_snapshot_response(row)
