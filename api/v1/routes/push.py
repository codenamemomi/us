from fastapi import APIRouter

from api.core.dependencies import CurrentUser, DatabaseSession
from api.v1.schema.push import SubIn, UnsubIn
from api.v1.services.push import subscribe_push, unsubscribe_push

router = APIRouter(prefix="/push", tags=["push"])


@router.post("/subscribe")
def post_subscribe(body: SubIn, user: CurrentUser, db: DatabaseSession) -> dict:
    subscribe_push(
        db=db,
        user_id=user.id,
        endpoint=body.endpoint,
        p256dh=body.keys.p256dh,
        auth=body.keys.auth,
    )
    return {"ok": True}


@router.post("/unsubscribe")
def post_unsubscribe(body: UnsubIn, user: CurrentUser, db: DatabaseSession) -> dict:
    unsubscribe_push(db=db, user_id=user.id, endpoint=body.endpoint)
    return {"ok": True}
