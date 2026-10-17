from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import BaseModel

if TYPE_CHECKING:
    from api.v1.models.answer import Answer
    from api.v1.models.couple import Couple
    from api.v1.models.question import Question


class DailyPrompt(BaseModel):
    __tablename__ = "daily_prompts"
    __table_args__ = (
        UniqueConstraint("couple_id", "prompt_date", name="uq_daily_prompts_couple_date"),
    )

    couple_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    prompt_date: Mapped[date] = mapped_column(Date, nullable=False)

    couple: Mapped[Couple] = relationship(back_populates="daily_prompts")
    question: Mapped[Question] = relationship(back_populates="daily_prompts")
    answers: Mapped[list[Answer]] = relationship(
        back_populates="prompt", cascade="all, delete-orphan"
    )