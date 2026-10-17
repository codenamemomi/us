from fastapi import FastAPI

from api.v1.routes import auth_router, couples_router
from api.v1.routes.engagement import router as engagement_router

app = FastAPI(title="US Backend", version="0.1.0")

app.include_router(auth_router)
app.include_router(couples_router)
app.include_router(engagement_router)


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
