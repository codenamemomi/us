from api.v1.games.base import BaseGame, REGISTRY, register
import api.v1.games.would_you_rather  # noqa: F401

__all__ = ["BaseGame", "REGISTRY", "register"]
