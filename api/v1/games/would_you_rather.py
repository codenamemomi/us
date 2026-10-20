from __future__ import annotations
import random
import re
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from api.v1.games.base import BaseGame, register
from api.v1.models.question import Question


def parse_wyr_options(text: str) -> tuple[str, str]:
    t = text.strip().rstrip("?")
    cleaned = re.sub(r"^[Ww]ould you rather\s+", "", t)
    parts = re.split(r",\s*or\s+|\s+or\s+", cleaned, maxsplit=1)
    if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
        # Capitalize first letter of each option
        opt_a = parts[0].strip()
        opt_b = parts[1].strip()
        return opt_a[0].upper() + opt_a[1:], opt_b[0].upper() + opt_b[1:]
    return "Option A", "Option B"


FALLBACK_QUESTIONS = [
    {
        "id": "fallback-1",
        "text": "Would you rather travel the world for a year with no home base, or build one perfect home and rarely leave it?",
        "option_a": "Travel the world for a year",
        "option_b": "Build one perfect home",
    },
    {
        "id": "fallback-2",
        "text": "Would you rather always know what I'm thinking, or never have to guess a movie's plot again?",
        "option_a": "Always know what I'm thinking",
        "option_b": "Never guess a movie's plot",
    },
    {
        "id": "fallback-3",
        "text": "Would you rather live by the beach or in the mountains?",
        "option_a": "Live by the beach",
        "option_b": "Live in the mountains",
    },
    {
        "id": "fallback-4",
        "text": "Would you rather cook together every night or order in and spend the time elsewhere?",
        "option_a": "Cook together every night",
        "option_b": "Order in and relax",
    },
    {
        "id": "fallback-5",
        "text": "Would you rather have a surprise party or a planned celebration?",
        "option_a": "Surprise party",
        "option_b": "Planned celebration",
    },
]


class WouldYouRather(BaseGame):
    type = "would_you_rather"

    def new_state(self, payload: dict[str, Any], db: Any = None) -> dict[str, Any]:
        rounds = []
        if db is not None:
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

        if not rounds:
            sample = random.sample(FALLBACK_QUESTIONS, min(5, len(FALLBACK_QUESTIONS)))
            for q in sample:
                rounds.append({"q": q, "picks": {}})

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
