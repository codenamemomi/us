import json
import logging
from uuid import UUID

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from api.core.config import settings
from api.v1.models import NotificationPref, PushSubscription
from api.v1.services.prefs import is_notification_suppressed

logger = logging.getLogger(__name__)


def subscribe_push(
    db: Session, user_id: UUID, endpoint: str, p256dh: str, auth: str
) -> PushSubscription:
    existing = db.query(PushSubscription).filter_by(endpoint=endpoint).first()
    if existing:
        existing.user_id = user_id
        existing.p256dh = p256dh
        existing.auth = auth
        sub = existing
    else:
        sub = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )
        db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def unsubscribe_push(db: Session, user_id: UUID, endpoint: str) -> bool:
    sub = (
        db.query(PushSubscription)
        .filter_by(endpoint=endpoint, user_id=user_id)
        .first()
    )
    if sub:
        db.delete(sub)
        db.commit()
        return True
    return False


def send_push(
    db: Session,
    user_id: UUID,
    title: str,
    body: str,
    url: str = "/",
    urgency: str = "normal",
    tag: str = "us-general",
) -> int:
    """Sends Web Push to all active push subscriptions for user_id.

    Returns the count of successfully delivered push notifications.
    Respects quiet hours and mute settings from NotificationPref.
    Cleans up 404/410 expired subscriptions.
    """
    pref = db.get(NotificationPref, user_id)
    if is_notification_suppressed(pref):
        logger.info(
            "Push notification suppressed by quiet hours or mute for user %s",
            user_id,
        )
        return 0

    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID keys not configured, skipping web push")
        return 0

    subs = db.query(PushSubscription).filter_by(user_id=user_id).all()
    if not subs:
        return 0

    delivered = 0
    to_delete = []

    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag})
    headers = {"Urgency": urgency}

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                headers=headers,
            )
            delivered += 1
        except WebPushException as exc:
            logger.warning("WebPush error for endpoint %s: %s", sub.endpoint, exc)
            if exc.response is not None and exc.response.status_code in (404, 410):
                to_delete.append(sub)
        except Exception as exc:
            logger.exception("Unexpected error sending push notification: %s", exc)

    if to_delete:
        for sub in to_delete:
            db.delete(sub)
        db.commit()

    return delivered
