from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
from api.v1.routes import auth_router, couples_router, push_router
from api.v1.routes.daily_prompt import router as daily_prompt_router
from api.v1.routes.engagement import router as engagement_router
from api.v1.routes.me import router as me_router

app = FastAPI(title="US Backend", version="0.1.0")

cors_origins = (
    settings.BACKEND_CORS_ORIGINS
    if isinstance(settings.BACKEND_CORS_ORIGINS, list)
    else [str(settings.BACKEND_CORS_ORIGINS)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(couples_router)
app.include_router(daily_prompt_router)
app.include_router(engagement_router)
app.include_router(me_router)
app.include_router(push_router)




@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
