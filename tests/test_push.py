from datetime import datetime, timedelta, timezone
from uuid import uuid4

from api.v1.models import NotificationPref
from api.v1.services.prefs import is_notification_suppressed


def test_is_notification_suppressed_when_muted():
    now = datetime.now(timezone.utc)
    pref = NotificationPref(id=uuid4(), muted_until=now + timedelta(hours=1))
    assert is_notification_suppressed(pref) is True

    pref_unmuted = NotificationPref(id=uuid4(), muted_until=now - timedelta(hours=1))
    assert is_notification_suppressed(pref_unmuted) is False


def test_is_notification_suppressed_none():
    assert is_notification_suppressed(None) is False
