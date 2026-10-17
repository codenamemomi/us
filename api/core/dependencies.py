from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from api.core.security import decode_access_token
from api.db.session import get_db
from api.v1.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DatabaseSession) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id: UUID = decode_access_token(token)
    except (JWTError, ValueError):
        raise credentials_error from None

    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


current_user = Annotated[User, Depends(get_current_user)]
CurrentUser = current_user