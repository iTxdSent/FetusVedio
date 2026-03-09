from fastapi import Depends, Header, HTTPException

from app.services.auth_service import AuthService, AuthUser

service = AuthService()


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix) :].strip()
    return ""


def get_current_user(authorization: str | None = Header(default=None)) -> AuthUser:
    token = extract_bearer_token(authorization)
    user = service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="未登录或登录已失效")
    return user


def get_auth_service() -> AuthService:
    return service
