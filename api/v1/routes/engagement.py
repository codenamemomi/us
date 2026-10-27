import asyncio
import json
import time
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.core.dependencies import CurrentUser, DatabaseSession
from api.core.realtime import hub
from api.core.security import decode_access_token
from api.v1.games import REGISTRY
from api.v1.models import BoredPing, CoupleStatus, GameSession, User
from api.v1.services.engagement import (
    couple_id_for,
    create_bored_ping,
    create_game,
    move_game,
    next_topic,
    partner_id_for,
    respond_to_ping,
    set_mode,
)

router = APIRouter(tags=["engagement"])


class ModeRequest(BaseModel):
    mode: str = Field(pattern="^(together|on_call|idle)$")


class BoredResponse(BaseModel):
    response: str = Field(pattern="^(join|give_me_10_min|cant_now)$")


class GameRequest(BaseModel):
    game_type: str = Field(min_length=1, max_length=64)


# ── Status ────────────────────────────────────────────────────────────────────
@router.get("/status")
def get_status(db: DatabaseSession, user: CurrentUser) -> dict:
    from api.v1.services.engagement import get_active_game

    couple_id = couple_id_for(db, user.id)
    status_row = db.get(CoupleStatus, couple_id)
    ping = (
        db.query(BoredPing)
        .filter(BoredPing.couple_id == couple_id, BoredPing.from_user != user.id, BoredPing.seen_at.is_(None))
        .order_by(BoredPing.created_at.desc())
        .first()
    )
    pid = partner_id_for(db, user.id)
    partner_online = hub.is_online(pid)
    active = get_active_game(db, user)
    return {
        "mode": status_row.mode if status_row else "idle",
        "unseen_bored_ping_id": ping.id if ping else None,
        "partner_online": partner_online,
        "active_game": {
            "id": str(active.id),
            "game_type": active.game_type,
            "created_by": str(active.created_by),
        }
        if active
        else None,
    }


@router.post("/status")
async def post_status(payload: ModeRequest, db: DatabaseSession, user: CurrentUser) -> dict:
    status_row = set_mode(db, user, payload.mode)
    pid = partner_id_for(db, user.id)
    await hub.publish(pid, {"type": "status_changed", "mode": payload.mode})
    return {"couple_id": status_row.id, "mode": status_row.mode, "set_by": status_row.set_by, "updated_at": status_row.updated_at}


# ── Bored Ping ────────────────────────────────────────────────────────────────
@router.post("/bored", status_code=status.HTTP_201_CREATED)
async def post_bored(db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        ping = create_bored_ping(db, user)
        pid = partner_id_for(db, user.id)
        await hub.publish(pid, {"type": "bored_ping", "ping_id": str(ping.id)})
        return {"ping_id": ping.id}
    except RuntimeError as error:
        raise HTTPException(429, str(error)) from error


@router.post("/bored/{ping_id}/respond")
def respond_bored(ping_id: UUID, payload: BoredResponse, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        ping = respond_to_ping(db, user, ping_id, payload.response)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    return {"id": ping.id, "response": ping.response}


# ── Topics ────────────────────────────────────────────────────────────────────
@router.get("/topics/next")
def get_next_topic(mode: str, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        card, question = next_topic(db, user, mode)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    return {"card_id": card.id, "question_id": question.id, "category": question.category, "text": question.text, "mode": card.mode}


# ── Games ─────────────────────────────────────────────────────────────────────
@router.get("/games/active")
def get_active_game_route(db: DatabaseSession, user: CurrentUser) -> dict:
    from api.v1.services.engagement import get_active_game

    active = get_active_game(db, user)
    if active is None:
        return {"active_game": None}
    engine = REGISTRY.get(active.game_type)
    state_view = engine.view_for(active.state, user.id) if engine else active.state
    return {
        "active_game": {
            "id": str(active.id),
            "game_type": active.game_type,
            "created_by": str(active.created_by),
            "state": state_view,
            "status": active.status,
        }
    }


@router.post("/games", status_code=status.HTTP_201_CREATED)
async def post_game(payload: GameRequest, db: DatabaseSession, user: CurrentUser) -> dict:
    from api.v1.services.engagement import create_or_join_game

    sess, is_new = create_or_join_game(db, user, payload.game_type)
    pid = partner_id_for(db, user.id)
    if is_new:
        await hub.publish(
            pid,
            {
                "type": "game_started",
                "game_id": str(sess.id),
                "game_type": sess.game_type,
                "started_by": str(user.id),
            },
        )
    await hub.publish(pid, {"type": "game_updated", "game_id": str(sess.id), "status": sess.status})
    engine = REGISTRY.get(sess.game_type)
    state_view = engine.view_for(sess.state, user.id) if engine else sess.state
    return {"id": sess.id, "game_type": sess.game_type, "state": state_view, "status": sess.status, "is_new": is_new}



@router.get("/games/{game_id}")
def get_game(game_id: UUID, db: DatabaseSession, user: CurrentUser) -> dict:
    sess = db.get(GameSession, game_id)
    if sess is None or sess.couple_id != couple_id_for(db, user.id):
        raise HTTPException(404, "Game not found")
    engine = REGISTRY.get(sess.game_type)
    state_view = engine.view_for(sess.state, user.id) if engine else sess.state
    return {"id": sess.id, "game_type": sess.game_type, "state": state_view, "status": sess.status}


@router.post("/games/{game_id}/move")
async def post_game_move(game_id: UUID, move: dict, db: DatabaseSession, user: CurrentUser) -> dict:
    try:
        sess, state_view = move_game(db, user, game_id, move)
        pid = partner_id_for(db, user.id)
        update_event = {"type": "game_updated", "game_id": str(sess.id), "status": sess.status}
        await hub.publish(pid, update_event)
        await hub.publish(user.id, update_event)
        return {"id": sess.id, "game_type": sess.game_type, "state": state_view, "status": sess.status}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


@router.delete("/games/{game_id}", status_code=status.HTTP_200_OK)
async def delete_game(game_id: UUID, db: DatabaseSession, user: CurrentUser) -> dict:
    """End / cancel an active game session. Both partners are notified via SSE."""
    from api.v1.services.engagement import end_game

    try:
        sess = end_game(db, user, game_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error

    pid = partner_id_for(db, user.id)
    ended_event = {"type": "game_ended", "game_id": str(sess.id)}
    # Notify both the partner and the caller's other tabs
    await hub.publish(pid, ended_event)
    await hub.publish(user.id, ended_event)
    return {"id": str(sess.id), "status": sess.status}


# ── Real-time SSE Stream ──────────────────────────────────────────────────────
@router.get("/stream")
async def get_stream(request: Request, db: DatabaseSession, token: str | None = None) -> StreamingResponse:
    # EventSource cannot set custom headers, so accept token from query or cookie or header
    auth_token = token
    if not auth_token:
        auth_hdr = request.headers.get("authorization")
        if auth_hdr and auth_hdr.lower().startswith("bearer "):
            auth_token = auth_hdr[7:].strip()
    if not auth_token:
        auth_token = request.cookies.get("access_token")

    if not auth_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authentication token")

    try:
        user_id = decode_access_token(auth_token)
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication token") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    pid = partner_id_for(db, user.id)
    was_online = hub.is_online(user.id)
    q: asyncio.Queue = asyncio.Queue()
    hub.subs[str(user.id)].add(q)
    hub.last_seen.pop(str(user.id), None)

    if not was_online and pid:
        await hub.publish(pid, {"type": "presence_changed", "partner_online": True})

    async def event_generator():
        try:
            # Initial event to confirm connection
            yield f"data: {json.dumps({'type': 'connected', 'user_id': str(user.id)})}\n\n"
            while not await request.is_disconnected():
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(ev)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            hub.subs[str(user.id)].discard(q)
            if len(hub.subs.get(str(user.id), set())) == 0:
                hub.last_seen[str(user.id)] = time.time()
                if pid:
                    async def notify_offline_after_grace(uid: str, partner_id: UUID):
                        await asyncio.sleep(4)
                        if len(hub.subs.get(uid, set())) == 0:
                            hub.last_seen.pop(uid, None)
                            await hub.publish(partner_id, {"type": "presence_changed", "partner_online": False})

                    hub.spawn(notify_offline_after_grace(str(user.id), pid))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )