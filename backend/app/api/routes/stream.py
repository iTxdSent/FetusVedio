import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect

from app.api.dependencies.auth import get_auth_service, get_current_user
from app.core.config import settings
from app.schemas.stream import SessionStateResponse, SpacingSetRequest, StartExamRequest, SwitchLocalVideoRequest
from app.services.auth_service import AuthService, AuthUser
from app.services.persistence import PersistenceService
from app.services.realtime.runtime import session_state_store, stream_processor

router = APIRouter(prefix="/stream")
ws_router = APIRouter()
service = PersistenceService()


def _to_state_response() -> SessionStateResponse:
    snapshot = session_state_store.get_snapshot()
    return SessionStateResponse(
        exam_active=snapshot.exam_active,
        freeze=snapshot.freeze,
        source_mode=snapshot.source_mode,
        source_state=snapshot.source_state,
        local_video_path=snapshot.local_video_path,
        frame_index=snapshot.frame_index,
        patient_id=snapshot.patient_id,
        session_id=snapshot.session_id,
        auto_capture_status=snapshot.auto_capture_status,
        user_id=snapshot.user_id,
        spacing_cm_per_pixel=snapshot.spacing_cm_per_pixel,
        spacing_confirmed=snapshot.spacing_confirmed,
    )


def _ensure_user_access(current_user: AuthUser) -> None:
    snap = session_state_store.get_snapshot()
    if snap.user_id is None:
        session_state_store.bind_user(current_user.id)
        return
    if snap.user_id != current_user.id and snap.exam_active:
        raise HTTPException(status_code=409, detail="当前有其他用户正在进行检查")
    if snap.user_id != current_user.id:
        session_state_store.bind_user(current_user.id)


@router.get("/state", response_model=SessionStateResponse)
def get_state(current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    return _to_state_response()


@router.post("/spacing", response_model=SessionStateResponse)
def set_spacing(payload: SpacingSetRequest, current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    session_state_store.set_spacing(payload.spacing_cm_per_pixel)
    session_state_store.set_auto_capture_status("比例尺已确认，可开始检查")
    return _to_state_response()


@router.post("/start", response_model=SessionStateResponse)
def start_exam(payload: StartExamRequest | None = None, current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)

    maybe_patient_id = payload.patient_id if payload else None
    if maybe_patient_id is not None:
        if service.get_patient(user_id=current_user.id, patient_id=maybe_patient_id) is None:
            raise HTTPException(status_code=404, detail="患者不存在")
        session_state_store.bind_patient(maybe_patient_id)

    snapshot = session_state_store.get_snapshot()
    if snapshot.patient_id is None:
        raise HTTPException(status_code=400, detail="请先绑定患者")
    if not snapshot.spacing_confirmed or snapshot.spacing_cm_per_pixel is None:
        raise HTTPException(status_code=409, detail="请先输入并确认比例尺")

    session = service.start_session(snapshot.patient_id)
    session_state_store.bind_session(session.id)
    stream_processor.reset_auto_capture()
    session_state_store.start_exam()
    return _to_state_response()


@router.post("/end", response_model=SessionStateResponse)
def end_exam(current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    snapshot = session_state_store.get_snapshot()
    if snapshot.session_id is not None:
        service.end_session(snapshot.session_id)
    stream_processor.reset_auto_capture()
    session_state_store.end_exam()
    session_state_store.clear_session()
    return _to_state_response()


@router.post("/freeze", response_model=SessionStateResponse)
def freeze_exam(current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    if not session_state_store.get_snapshot().exam_active:
        raise HTTPException(status_code=409, detail="检查未开始，无法冻结")
    session_state_store.freeze_exam()
    return _to_state_response()


@router.post("/unfreeze", response_model=SessionStateResponse)
def unfreeze_exam(current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    if not session_state_store.get_snapshot().exam_active:
        raise HTTPException(status_code=409, detail="检查未开始，无法解冻")
    session_state_store.unfreeze_exam()
    return _to_state_response()


@router.post("/switch-local-video", response_model=SessionStateResponse)
def switch_local_video(
    payload: SwitchLocalVideoRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> SessionStateResponse:
    _ensure_user_access(current_user)
    path = Path(payload.video_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=400, detail="本地视频文件不存在")
    session_state_store.switch_local_video(str(path))
    return _to_state_response()


@router.post("/upload-local-video", response_model=SessionStateResponse)
async def upload_local_video(
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
) -> SessionStateResponse:
    _ensure_user_access(current_user)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".mp4", ".avi", ".mov", ".mkv", ".m4v"}:
        raise HTTPException(status_code=400, detail="不支持的视频格式")

    upload_dir = Path(settings.local_video_upload_dir).expanduser().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{uuid4().hex}{suffix}"

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="上传文件为空")
    saved_path.write_bytes(content)

    session_state_store.switch_local_video(str(saved_path))
    return _to_state_response()


@router.post("/resume-capture", response_model=SessionStateResponse)
def resume_capture(current_user: AuthUser = Depends(get_current_user)) -> SessionStateResponse:
    _ensure_user_access(current_user)
    session_state_store.resume_capture()
    return _to_state_response()


@router.post("/manual-save")
def manual_save(current_user: AuthUser = Depends(get_current_user)) -> dict:
    _ensure_user_access(current_user)
    row = stream_processor.manual_save_snapshot()
    if row is None:
        raise HTTPException(status_code=409, detail="当前无可保存帧")
    return {
        "snapshot_id": row.id,
        "overlay_url": f"/media/{row.overlay_path}",
        "message": "手动保存成功",
    }


@ws_router.websocket("/ws/stream")
async def stream_ws(
    websocket: WebSocket,
    token: str = Query(default=""),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    user = auth_service.get_user_by_token(token)
    if user is None:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            snap = session_state_store.get_snapshot()
            if snap.user_id is not None and snap.user_id != user.id and snap.exam_active:
                await websocket.send_json({"error": "当前会话由其他用户占用"})
            else:
                await websocket.send_json(stream_processor.get_latest_payload())
            await asyncio.sleep(1.0 / max(1, settings.stream_fps))
    except (WebSocketDisconnect, RuntimeError):
        return
