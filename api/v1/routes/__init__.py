from api.v1.routes.auth import router as auth_router
from api.v1.routes.couples import router as couples_router
from api.v1.routes.push import router as push_router

__all__ = ["auth_router", "couples_router", "push_router"]
