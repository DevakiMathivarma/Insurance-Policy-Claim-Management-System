import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # jwt
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # redis
    REDIS_HOST: str = os.getenv("REDIS_HOST")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str | None = os.getenv("REDIS_PASSWORD")

    # celery - separate redis db numbers from the cache, so celery's own
    # bookkeeping never mixes with cached data
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # smtp
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL")

    # default super admin
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@12345")
    DEFAULT_ADMIN_PHONE: str = os.getenv("DEFAULT_ADMIN_PHONE", "9999999999")

    # rate limiting
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 5))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

    # file uploads - claim documents
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", 10))
    ALLOWED_UPLOAD_EXTENSIONS: list = os.getenv("ALLOWED_UPLOAD_EXTENSIONS", "pdf,jpg,jpeg,png").split(",")


settings = Settings()