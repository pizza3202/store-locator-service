from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(payload: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token_payload = {**payload, "exp": expire}
    return jwt.encode(token_payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(payload: dict[str, Any]) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    token_payload = {**payload, "exp": expire}
    token = jwt.encode(token_payload, settings.secret_key, algorithm=ALGORITHM)
    return token, expire


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
