from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.db.base import BaseModel


class CoupleStatus(BaseModel):
    __tablename__ = "couple_status"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("couples.id"), primary_key=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    set_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BoredPing(BaseModel):
    __tablename__ = "bored_pings"

    couple_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("couples.id"), nullable=False)
    from_user: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response: Mapped[str | None] = mapped_column(String(32))


class GameSession(BaseModel):
    __tablename__ = "game_sessions"

    couple_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("couples.id"), nullable=False)
    game_type: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB().with_variant(JSON, "sqlite"), nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TopicCard(BaseModel):
    __tablename__ = "topic_cards"

    couple_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("couples.id"), nullable=False)
    question_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)


class NotificationPref(BaseModel):
    __tablename__ = "notification_prefs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    email_on_bored: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5))
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5))
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))