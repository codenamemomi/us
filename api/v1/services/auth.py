from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.core.security import hash_password, verify_password
from api.v1.models.couple import Couple
from api.v1.models.couple_member import CoupleMember
from api.v1.models.user import User
from api.v1.schema.auth import LoginRequest, RegisterRequest
from api.v1.services.errors import (
    CoupleFullError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidInviteCodeError,
)


def register_user(db: Session, request: RegisterRequest) -> tuple[User, Couple]:
    couple = db.scalar(
        select(Couple).where(Couple.invite_code == request.invite_code)
    )
    if couple is None:
        raise InvalidInviteCodeError()

    member_count = db.scalar(
        select(func.count())
        .select_from(CoupleMember)
        .where(CoupleMember.couple_id == couple.id)
    )
    if member_count >= 2:
        raise CoupleFullError()

    email = request.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise EmailAlreadyRegisteredError()

    user = User(
        name=request.name,
        email=email,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.flush()
    db.add(CoupleMember(couple_id=couple.id, user_id=user.id))

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegisteredError() from error

    db.refresh(user)
    return user, couple


def authenticate_user(db: Session, request: LoginRequest) -> User:
    email = request.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError()
    return user