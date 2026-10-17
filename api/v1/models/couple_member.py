from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base

if TYPE_CHECKING:
    from api.v1.models.couple import Couple
    from api.v1.models.user import User


class CoupleMember(Base):
    __tablename__ = "couple_members"

    couple_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    couple: Mapped[Couple] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="couple_members")