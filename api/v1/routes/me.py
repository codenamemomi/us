from fastapi import APIRouter

from api.core.dependencies import CurrentUser, DatabaseSession
from api.v1.schema.prefs import PrefsOut, PrefsUpdate
from api.v1.services.prefs import get_or_create_prefs, serialize_prefs, update_prefs

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/prefs", response_model=PrefsOut)
def get_prefs(db: DatabaseSession, user: CurrentUser) -> PrefsOut:
    return serialize_prefs(get_or_create_prefs(db, user))


@router.patch("/prefs", response_model=PrefsOut)
@router.post("/prefs", response_model=PrefsOut)
def patch_prefs(payload: PrefsUpdate, db: DatabaseSession, user: CurrentUser) -> PrefsOut:
    return serialize_prefs(update_prefs(db, user, payload))
