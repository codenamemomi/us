from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from api.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID:
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.jwt_algorithm]
    )
    subject = payload.get("sub")
    if not subject:
        raise JWTError("Token subject is missing")
    return UUID(subject)