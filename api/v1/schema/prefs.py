from __future__ import annotations

from pydantic import BaseModel, Field


class PrefsOut(BaseModel):
    email_on_bored: bool
    quiet_hours_start: str | None = None   # "HH:MM"
    quiet_hours_end: str | None = None     # "HH:MM"
    muted: bool = False
    muted_until: str | None = None         # ISO datetime when mute expires


class PrefsUpdate(BaseModel):
    email_on_bored: bool | None = None
    quiet_hours_start: str | None = Field(
        default=None,
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="24-h time string HH:MM, e.g. '22:00'",
    )
    quiet_hours_end: str | None = Field(
        default=None,
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="24-h time string HH:MM, e.g. '07:00'",
    )
    # positive = mute for N minutes, 0 or omit = no change, -1 = unmute
    mute_minutes: int | None = Field(default=None, ge=-1)
    unmute: bool | None = None
