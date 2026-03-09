from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from sqlalchemy import select

from app.db.models import User, UserSession
from app.db.session import SessionLocal


@dataclass(frozen=True)
class AuthUser:
    id: int
    username: str


class AuthService:
    def _hash_password(self, password: str, salt_hex: str) -> str:
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            120_000,
        )
        return digest.hex()

    def register(self, username: str, password: str) -> User:
        uname = username.strip()
        if not uname:
            raise ValueError("用户名不能为空")

        with SessionLocal() as db:
            exists = db.execute(select(User).where(User.username == uname)).scalars().first()
            if exists is not None:
                raise ValueError("用户名已存在")

            salt_hex = secrets.token_hex(16)
            pwd_hash = self._hash_password(password, salt_hex)
            row = User(username=uname, password_salt=salt_hex, password_hash=pwd_hash)
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    def verify_user(self, username: str, password: str) -> User | None:
        uname = username.strip()
        with SessionLocal() as db:
            user = db.execute(select(User).where(User.username == uname)).scalars().first()
            if user is None:
                return None
            pwd_hash = self._hash_password(password, user.password_salt)
            if secrets.compare_digest(pwd_hash, user.password_hash):
                return user
            return None

    def create_token(self, user_id: int) -> str:
        token = secrets.token_urlsafe(48)
        with SessionLocal() as db:
            row = UserSession(user_id=user_id, token=token, revoked=False)
            db.add(row)
            db.commit()
        return token

    def get_user_by_token(self, token: str) -> AuthUser | None:
        tok = token.strip()
        if not tok:
            return None

        with SessionLocal() as db:
            session = (
                db.execute(select(UserSession).where(UserSession.token == tok, UserSession.revoked.is_(False)))
                .scalars()
                .first()
            )
            if session is None:
                return None
            user = db.get(User, session.user_id)
            if user is None:
                return None
            return AuthUser(id=user.id, username=user.username)

    def revoke_token(self, token: str) -> None:
        tok = token.strip()
        if not tok:
            return
        with SessionLocal() as db:
            session = db.execute(select(UserSession).where(UserSession.token == tok)).scalars().first()
            if session is None:
                return
            session.revoked = True
            db.add(session)
            db.commit()

    def get_user_info(self, user_id: int) -> User | None:
        with SessionLocal() as db:
            return db.get(User, user_id)
