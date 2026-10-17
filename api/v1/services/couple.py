import secrets
import string

from sqlalchemy.orm import Session

from api.v1.models.couple import Couple


def _new_invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def create_couple(db: Session) -> Couple:
    couple = Couple(invite_code=_new_invite_code())
    db.add(couple)
    db.commit()
    db.refresh(couple)
    return couple