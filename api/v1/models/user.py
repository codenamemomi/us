from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.answer import Answer
    from api.v1.models.couple_member import CoupleMember
    from api.v1.models.event import Event


class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    couple_members: Mapped[list[CoupleMember]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    answers: Mapped[list[Answer]] = relationship(back_populates="user")
    events: Mapped[list[Event]] = relationship(back_populates="user")