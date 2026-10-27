from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.couple_member import CoupleMember
    from api.v1.models.daily_prompt import DailyPrompt
    from api.v1.models.event import Event


class Couple(BaseModel):
    __tablename__ = "couples"

    invite_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    anniversary_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    members: Mapped[list[CoupleMember]] = relationship(
        back_populates="couple", cascade="all, delete-orphan"
    )
    daily_prompts: Mapped[list[DailyPrompt]] = relationship(
        back_populates="couple", cascade="all, delete-orphan"
    )
    events: Mapped[list[Event]] = relationship(back_populates="couple")