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
    invite_code = request.invite_code.strip().upper()
    couple = db.scalar(
        select(Couple).where(Couple.invite_code == invite_code)
    )
    if couple is None:
        raise InvalidInviteCodeError()

    existing_members = db.scalars(
        select(CoupleMember).where(CoupleMember.couple_id == couple.id)
    ).all()
    member_count = len(existing_members)
    if member_count >= 2:
        raise CoupleFullError()

    email = str(request.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise EmailAlreadyRegisteredError()

    user = User(
        name=request.name.strip(),
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

    # ── Sweet welcome / couple complete emails ──────────────────────────────
    from api.utils.email import (
        send_async,
        send_couple_connected_email,
        send_welcome_account_email,
    )

    if member_count == 0:
        # First partner: account created, couple waiting for partner
        send_async(send_welcome_account_email, user.email, user.name, couple.invite_code)
    elif member_count == 1:
        # Second partner registered: couple is now complete!
        partner_member = existing_members[0]
        partner_user = db.get(User, partner_member.user_id)
        if partner_user:
            send_async(send_couple_connected_email, user.email, user.name, partner_user.name)
            send_async(send_couple_connected_email, partner_user.email, partner_user.name, user.name)

    return user, couple


def authenticate_user(db: Session, request: LoginRequest) -> User:
    email = str(request.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError()
    return user