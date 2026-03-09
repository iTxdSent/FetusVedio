from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfoResponse(BaseModel):
    id: int
    username: str
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserInfoResponse
