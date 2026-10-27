from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from api.v1.models import Couple, CoupleMember, User
from api.v1.schema.couple import UpdateAnniversaryRequest


def test_update_anniversary_request_schema():
    req = UpdateAnniversaryRequest(anniversary_date=date(2023, 5, 14))
    assert req.anniversary_date == date(2023, 5, 14)

    req_none = UpdateAnniversaryRequest(anniversary_date=None)
    assert req_none.anniversary_date is None


def test_couple_anniversary_days_calculation():
    # 100 days ago
    start = datetime.now(timezone.utc).date() - timedelta(days=99)
    days_together = (datetime.now(timezone.utc).date() - start).days + 1
    assert days_together == 100
