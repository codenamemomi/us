from pydantic import BaseModel


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class SubIn(BaseModel):
    endpoint: str
    keys: PushKeys
    expirationTime: int | None = None


class UnsubIn(BaseModel):
    endpoint: str
