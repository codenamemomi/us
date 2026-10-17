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


def create_game(db: Session, user: User, game_type: str) -> GameSession:
    game = GameSession(couple_id=couple_id_for(db, user.id), game_type=game_type, created_by=user.id, state={})
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def move_game(db: Session, user: User, game_id: UUID, move: dict) -> GameSession:
    game = db.get(GameSession, game_id)
    if game is None or game.couple_id != couple_id_for(db, user.id):
        raise LookupError("Game not found")
    game.state = {**game.state, "last_move": {"user_id": str(user.id), **move}}
    db.commit()
    db.refresh(game)
    return game