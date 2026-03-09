from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.dependencies.auth import extract_bearer_token, get_auth_service, get_current_user
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserInfoResponse
from app.services.auth_service import AuthService, AuthUser

router = APIRouter(prefix="/auth")


def _to_user_info(user_row) -> UserInfoResponse:
    return UserInfoResponse(id=user_row.id, username=user_row.username, created_at=user_row.created_at)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    try:
        user = service.register(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = service.create_token(user.id)
    return AuthResponse(token=token, user=_to_user_info(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    user = service.verify_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = service.create_token(user.id)
    return AuthResponse(token=token, user=_to_user_info(user))


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    _: AuthUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    token = extract_bearer_token(authorization)
    service.revoke_token(token)
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserInfoResponse)
def me(current_user: AuthUser = Depends(get_current_user), service: AuthService = Depends(get_auth_service)) -> UserInfoResponse:
    row = service.get_user_info(current_user.id)
    if row is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return _to_user_info(row)
