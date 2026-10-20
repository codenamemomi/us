from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "US Backend"
    APP_PUBLIC_NAME: str = "US"
    SECRET_KEY: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    DATABASE_URL: str = "sqlite:///./us.db"

    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    BACKEND_CORS_ORIGINS: list[str] | str = ["http://localhost:3000"]

    PAYSTACK_SECRET_KEY: str | None = None
    PAYSTACK_PUBLIC_KEY: str | None = None
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"
    PAYSTACK_CALLBACK_URL: str | None = None
    PAYSTACK_CURRENCY: str = "NGN"

    EMAIL_PROVIDER: str = "console"
    EMAIL_FROM: str = "no-reply@us.app"
    EMAIL_ASYNC: bool = False
    BREVO_API_KEY: str | None = None
    OTP_TTL_SECONDS: int = 300
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    VAPID_PUBLIC_KEY: str | None = None
    VAPID_PRIVATE_KEY: str | None = None
    VAPID_SUBJECT: str = "mailto:you@omomi.me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()