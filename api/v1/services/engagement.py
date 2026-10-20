from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.v1.models import BoredPing, CoupleMember, CoupleStatus, GameSession, Question, TopicCard, User


def couple_id_for(db: Session, user_id: UUID) -> UUID:
    member = db.scalar(select(CoupleMember).where(CoupleMember.user_id == user_id))
    if member is None:
        raise ValueError("User is not a member of a couple")
    return member.couple_id


def set_mode(db: Session, user: User, mode: str) -> CoupleStatus:
    couple_id = couple_id_for(db, user.id)
    status = db.get(CoupleStatus, couple_id)
    if status is None:
        status = CoupleStatus(id=couple_id, mode=mode, set_by=user.id)
        db.add(status)
    else:
        status.mode = mode
        status.set_by = user.id
        status.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(status)
    return status


def create_bored_ping(db: Session, user: User) -> BoredPing:
    couple_id = couple_id_for(db, user.id)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    recent = db.scalar(select(BoredPing).where(BoredPing.from_user == user.id, BoredPing.created_at >= cutoff))
    if recent is not None:
        raise RuntimeError("You pinged recently, give them a minute")
    ping = BoredPing(couple_id=couple_id, from_user=user.id)
    db.add(ping)
    db.commit()
    db.refresh(ping)

    # If partner is offline, send push notification or email fallback
    pid = partner_id_for(db, user.id)
    if pid:
        from api.core.realtime import hub
        from api.v1.models import NotificationPref
        from api.v1.services.prefs import is_notification_suppressed
        from api.v1.services.push import send_push
        from api.utils.email import send_bored_email

        if not hub.is_online(pid):
            pref = db.get(NotificationPref, pid)
            if not is_notification_suppressed(pref):
                push_count = send_push(
                    db=db,
                    user_id=pid,
                    title="us.",
                    body=f"{user.name} is bored 👀 · Tap to join",
                    url="/",
                    urgency="high",
                    tag="bored",
                )
                if push_count == 0:
                    email_enabled = pref.email_on_bored if pref else True
                    if email_enabled:
                        partner = db.get(User, pid)
                        if partner and partner.email:
                            send_bored_email(partner.email, partner.name, user.name)

    return ping


def respond_to_ping(db: Session, user: User, ping_id: UUID, response: str) -> BoredPing:
    ping = db.get(BoredPing, ping_id)
    if ping is None or ping.couple_id != couple_id_for(db, user.id) or ping.from_user == user.id:
        raise LookupError("Bored ping not found")
    ping.response = response
    ping.seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ping)
    return ping


def next_topic(db: Session, user: User, mode: str) -> tuple[TopicCard, Question]:
    couple_id = couple_id_for(db, user.id)
    question = db.scalar(
        select(Question).where(
            Question.active.is_(True),
            Question.category != "spicy_18",
            ~Question.id.in_(select(TopicCard.question_id).where(TopicCard.couple_id == couple_id)),
        ).order_by(func.random())
    )
    if question is None:
        raise LookupError("No undisplayed topics remain")
    card = TopicCard(couple_id=couple_id, question_id=question.id, mode=mode)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card, question


def partner_id_for(db: Session, user_id: UUID) -> UUID | None:
    try:
        couple_id = couple_id_for(db, user_id)
    except ValueError:
        return None
    member = db.scalars(
        select(CoupleMember).where(
            CoupleMember.couple_id == couple_id, CoupleMember.user_id != user_id
        )
    ).first()
    return member.user_id if member else None


def get_active_game(db: Session, user: User) -> GameSession | None:
    couple_id = couple_id_for(db, user.id)
    return (
        db.query(GameSession)
        .filter(GameSession.couple_id == couple_id, GameSession.status == "active")
        .order_by(GameSession.created_at.desc())
        .first()
    )


def create_or_join_game(db: Session, user: User, game_type: str) -> tuple[GameSession, bool]:
    """Returns (session, is_new). If an active session exists for this couple, reuses it!"""
    active = get_active_game(db, user)
    if active is not None:
        return active, False

    from api.v1.games import REGISTRY

    couple_id = couple_id_for(db, user.id)
    engine = REGISTRY.get(game_type)
    initial_state = engine.new_state({"couple_id": str(couple_id)}, db=db) if engine else {}
    game = GameSession(couple_id=couple_id, game_type=game_type, created_by=user.id, state=initial_state)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game, True


def create_game(db: Session, user: User, game_type: str) -> GameSession:
    sess, _ = create_or_join_game(db, user, game_type)
    return sess


def move_game(db: Session, user: User, game_id: UUID, move: dict) -> tuple[GameSession, dict]:
    from sqlalchemy.orm.attributes import flag_modified
    from api.v1.games import REGISTRY

    couple_id = couple_id_for(db, user.id)
    game = db.query(GameSession).filter_by(id=game_id, couple_id=couple_id).with_for_update().first()
    if game is None:
        raise LookupError("Game not found")

    engine = REGISTRY.get(game.game_type)
    if engine is None:
        game.state = {**game.state, "last_move": {"user_id": str(user.id), **move}}
        flag_modified(game, "state")
        db.commit()
        db.refresh(game)
        return game, game.state

    new_state = engine.apply_move(game.state, user.id, move)
    game.state = new_state
    flag_modified(game, "state")
    game.status = "done" if engine.is_done(game.state) else "active"
    db.commit()
    db.refresh(game)
    return game, engine.view_for(game.state, user.id)


def end_game(db: Session, user: User, game_id: UUID) -> GameSession:
    """Mark an active game session as cancelled. Either partner may end the session."""
    couple_id = couple_id_for(db, user.id)
    game = db.query(GameSession).filter_by(id=game_id, couple_id=couple_id).with_for_update().first()
    if game is None:
        raise LookupError("Game not found")
    if game.status not in ("active",):
        # Already finished or cancelled — still OK, just return it
        return game
    game.status = "cancelled"
    db.commit()
    db.refresh(game)
    return game