from __future__ import annotations
import re
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from api.v1.games.base import BaseGame, register
from api.v1.models.question import Question


def parse_wyr_options(text: str) -> tuple[str, str]:
    t = text.strip()
    # Remove leading 'Would you rather' (case-insensitive, handles optional colons/dashes/spaces)
    cleaned = re.sub(r"^[Ww]ould you rather[:,\s\-]*", "", t, flags=re.IGNORECASE).strip()
    # Remove trailing question marks or punctuation
    cleaned = cleaned.rstrip("?!. ")

    # Split on the word 'or' (case-insensitive, handles optional comma before 'or')
    parts = re.split(r",?\s*\bor\b\s*", cleaned, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
        opt_a = parts[0].strip().rstrip(",; ")
        opt_b = parts[1].strip().rstrip("?!. ")
        if opt_a and opt_b:
            return opt_a[0].upper() + opt_a[1:], opt_b[0].upper() + opt_b[1:]

    return "Option A", "Option B"


class WouldYouRather(BaseGame):
    type = "would_you_rather"

    def new_state(self, payload: dict[str, Any], db: Any = None) -> dict[str, Any]:
        rounds = []
        session_to_close = None
        if db is None:
            from api.db.session import SessionLocal
            db = SessionLocal()
            session_to_close = db

        try:
            db_questions = db.scalars(
                select(Question)
                .where(Question.category == "would_you_rather", Question.active.is_(True))
                .order_by(func.random())
                .limit(5)
            ).all()
            for q in db_questions:
                opt_a, opt_b = parse_wyr_options(q.text)
                rounds.append({
                    "q": {
                        "id": str(q.id),
                        "text": q.text,
                        "option_a": opt_a,
                        "option_b": opt_b,
                    },
                    "picks": {},
                })
        finally:
            if session_to_close is not None:
                session_to_close.close()

        return {"rounds": rounds, "current": 0}

    def apply_move(self, state: dict[str, Any], user_id: str | UUID, move: dict[str, Any]) -> dict[str, Any]:
        rounds = state.get("rounds", [])
        curr_idx = state.get("current", 0)
        if not rounds or curr_idx >= len(rounds):
            return state

        # Handle advance next round
        if move.get("action") == "next":
            rnd = rounds[curr_idx]
            if len(rnd.get("picks", {})) == 2 and curr_idx < len(rounds) - 1:
                state["current"] = curr_idx + 1
            return state

        rnd = rounds[curr_idx]
        uid = str(user_id)
        if uid in rnd.get("picks", {}):
            raise ValueError("already picked")

        choice = str(move.get("choice", "")).lower()
        if choice not in ("a", "b"):
            raise ValueError("Choice must be 'a' or 'b'")

        rnd.setdefault("picks", {})[uid] = choice
        return state

    def view_for(self, state: dict[str, Any], user_id: str | UUID) -> dict[str, Any]:
        uid = str(user_id)
        rounds = state.get("rounds", [])
        out = []

        for rnd in rounds:
            picks = rnd.get("picks", {})
            both = len(picks) == 2
            my_pick = picks.get(uid)
            partner_picked = both or any(k != uid for k in picks)
            partner_pick = next((v for k, v in picks.items() if k != uid), None) if both else None
            matched = both and len(picks) == 2 and len(set(picks.values())) == 1

            out.append({
                "q": rnd.get("q", {}),
                "my_pick": my_pick,
                "partner_picked": partner_picked,
                "partner_pick": partner_pick,
                "both_picked": both,
                "matched": matched,
            })

        matches = sum(1 for r in out if r["matched"])
        curr_idx = state.get("current", 0)

        return {
            "type": self.type,
            "rounds": out,
            "current": curr_idx,
            "matches": matches,
            "total_rounds": len(out),
            "is_done": self.is_done(state),
        }

    def is_done(self, state: dict[str, Any]) -> bool:
        rounds = state.get("rounds", [])
        return bool(rounds) and all(len(r.get("picks", {})) == 2 for r in rounds)


register(WouldYouRather())
