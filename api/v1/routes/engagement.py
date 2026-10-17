from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.core.dependencies import CurrentUser, DatabaseSession
from api.v1.services.engagement import create_bored_ping, create_game, move_game, next_topic, respond_to_ping, set_mode

router = APIRouter(tags=["engagement"])


class ModeRequest(BaseModel):
    mode: str = Field(pattern="^(together|on_call|idle)$")


class BoredResponse(BaseModel):
    response: str = Field(pattern="^(join|give_me_10_min|cant_now)$")


class GameRequest(BaseModel):
    game_type: str = Field(min_length=1, max_length=64)


@router.get("/status")
def get_status(db: DatabaseSession, user: CurrentUser) -> dict:
    from api.v1.services.engagement import couple_id_for
    from api.v1.models import BoredPing, CoupleStatus
    couple_id = couple_id_for(db, user.id)
    status_row = db.get(CoupleStatus, couple_id)
    ping = db.query(BoredPing).filter(BoredPing.couple_id == couple_id, BoredPing.from_user != user.id, BoredPing.seen_at.is_(None)).order_by(BoredPing.created_at.desc()).first()
    return {"mode": status_row.mode if status_row else "idle", "unseen_bored_ping_id": ping.id if ping else None}


@router.post("/status")
def post_status(payload: ModeRequest, db: DatabaseSession, user: CurrentUser) -> dict:
    status_row = set_mode(db, user, payload.mode)
    return {"couple_id": status_row.id, "mode": status_row.mode, "set_by": status_row.set_by, "updated_at": status_row.updated_at}


@router.post("/bored", status_code=status.HTTP_201_CREATED)
def post_bored(db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        return {"ping_id": create_bored_ping(db, user).id}
    except RuntimeError as error:
        raise HTTPException(429, str(error)) from error


@router.post("/bored/{ping_id}/respond")
def respond_bored(ping_id: UUID, payload: BoredResponse, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        ping = respond_to_ping(db, user, ping_id, payload.response)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    return {"id": ping.id, "response": ping.response}


@router.get("/topics/next")
def get_next_topic(mode: str, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        card, question = next_topic(db, user, mode)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    return {"card_id": card.id, "question_id": question.id, "category": question.category, "text": question.text, "mode": card.mode}


@router.post("/games", status_code=status.HTTP_201_CREATED)
def post_game(payload: GameRequest, db: DatabaseSession, user: CurrentUser) -> dict:
    game = create_game(db, user, payload.game_type)
    return {"id": game.id, "game_type": game.game_type, "state": game.state, "status": game.status}


@router.get("/games/{game_id}")
def get_game(game_id: UUID, db: DatabaseSession, user: CurrentUser) -> dict:
    from api.v1.services.engagement import couple_id_for
    from api.v1.models import GameSession
    game = db.get(GameSession, game_id)
    if game is None or game.couple_id != couple_id_for(db, user.id):
        raise HTTPException(404, "Game not found")
    return {"id": game.id, "game_type": game.game_type, "state": game.state, "status": game.status}


@router.post("/games/{game_id}/move")
def post_game_move(game_id: UUID, move: dict, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        game = move_game(db, user, game_id, move)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    return {"id": game.id, "state": game.state, "status": game.status}