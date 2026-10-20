from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from api.v1.models import NotificationPref, User
from api.v1.schema.prefs import PrefsOut, PrefsUpdate


def get_or_create_prefs(db: Session, user: User) -> NotificationPref:
    prefs = db.get(NotificationPref, user.id)
    if prefs is None:
        prefs = NotificationPref(id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def update_prefs(db: Session, user: User, payload: PrefsUpdate) -> NotificationPref:
    prefs = get_or_create_prefs(db, user)

    if payload.email_on_bored is not None:
        prefs.email_on_bored = payload.email_on_bored

    if payload.quiet_hours_start is not None:
        prefs.quiet_hours_start = payload.quiet_hours_start

    if payload.quiet_hours_end is not None:
        prefs.quiet_hours_end = payload.quiet_hours_end

    if payload.mute_minutes is not None:
        if payload.mute_minutes <= 0:
            prefs.muted_until = None
        else:
            from datetime import timedelta
            prefs.muted_until = datetime.now(timezone.utc) + timedelta(minutes=payload.mute_minutes)

    if payload.unmute is True:
        prefs.muted_until = None

    db.commit()
    db.refresh(prefs)
    return prefs


def serialize_prefs(prefs: NotificationPref) -> PrefsOut:
    now = datetime.now(timezone.utc)
    muted = prefs.muted_until is not None and prefs.muted_until > now
    muted_until_iso = prefs.muted_until.isoformat() if muted else None
    return PrefsOut(
        email_on_bored=prefs.email_on_bored,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        muted=muted,
        muted_until=muted_until_iso,
    )


def is_notification_suppressed(prefs: NotificationPref | None) -> bool:
    if not prefs:
        return False
    now = datetime.now(timezone.utc)
    if prefs.muted_until and prefs.muted_until > now:
        return True
    if prefs.quiet_hours_start and prefs.quiet_hours_end:
        try:
            start_parts = [int(p) for p in prefs.quiet_hours_start.split(":")]
            end_parts = [int(p) for p in prefs.quiet_hours_end.split(":")]
            from datetime import time as dtime
            start_time = dtime(start_parts[0], start_parts[1])
            end_time = dtime(end_parts[0], end_parts[1])
            current_time = now.time()
            if start_time <= end_time:
                if start_time <= current_time <= end_time:
                    return True
            else:
                if current_time >= start_time or current_time <= end_time:
                    return True
        except Exception:
            pass
    return False

