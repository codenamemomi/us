from datetime import datetime, timedelta, timezone
import secrets
import string
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.v1.models import Answer, Couple, CoupleMember, DailyPrompt, User
from api.v1.schema.couple import CoupleProfileResponse, PartnerInfo


def _new_invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def create_couple(db: Session) -> Couple:
    couple = Couple(invite_code=_new_invite_code())
    db.add(couple)
    db.commit()
    db.refresh(couple)
    return couple


def calculate_streak(db: Session, couple_id: UUID) -> int:
    answered_dates = db.scalars(
        select(DailyPrompt.prompt_date)
        .join(Answer, Answer.prompt_id == DailyPrompt.id)
        .where(DailyPrompt.couple_id == couple_id)
        .distinct()
        .order_by(DailyPrompt.prompt_date.desc())
    ).all()

    if not answered_dates:
        return 1

    date_set = set(answered_dates)
    today = datetime.now(timezone.utc).date()

    current_check = today if today in date_set else (today - timedelta(days=1))
    if current_check not in date_set:
        return 1

    streak = 0
    while current_check in date_set:
        streak += 1
        current_check -= timedelta(days=1)

    return max(1, streak)


def get_couple_profile(db: Session, user: User) -> CoupleProfileResponse:
    from api.v1.services.engagement import couple_id_for

    couple_id = couple_id_for(db, user.id)
    couple = db.get(Couple, couple_id)
    if couple is None:
        raise ValueError("Couple not found")

    members = db.scalars(
        select(CoupleMember).where(CoupleMember.couple_id == couple_id)
    ).all()

    partner_member = next((m for m in members if m.user_id != user.id), None)
    partner_user = db.get(User, partner_member.user_id) if partner_member else None

    days_together = max(1, (datetime.now(timezone.utc).date() - couple.created_at.date()).days + 1)
    streak = calculate_streak(db, couple_id)

    return CoupleProfileResponse(
        couple_id=couple.id,
        invite_code=couple.invite_code,
        created_at=couple.created_at,
        me=PartnerInfo(id=user.id, name=user.name, email=user.email),
        partner=PartnerInfo(id=partner_user.id, name=partner_user.name, email=partner_user.email)
        if partner_user
        else None,
        streak=streak,
        days_together=days_together,
    )