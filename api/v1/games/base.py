from __future__ import annotations
from typing import Any
from uuid import UUID


class BaseGame:
    type: str

    def new_state(self, payload: dict[str, Any], db: Any = None) -> dict[str, Any]:
        raise NotImplementedError

    def apply_move(self, state: dict[str, Any], user_id: str | UUID, move: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def view_for(self, state: dict[str, Any], user_id: str | UUID) -> dict[str, Any]:
        """Hides partner's secrets until revealed."""
        raise NotImplementedError

    def is_done(self, state: dict[str, Any]) -> bool:
        raise NotImplementedError


REGISTRY: dict[str, BaseGame] = {}


def register(game: BaseGame) -> None:
    REGISTRY[game.type] = game
