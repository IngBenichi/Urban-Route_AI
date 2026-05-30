from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://urbanroute:changeme@localhost:5432/urbanroutedb"
    SYNC_DATABASE_URL: str = "postgresql://urbanroute:changeme@localhost:5432/urbanroutedb"

    # JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme-admin-password"

    # Grok AI
    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-3-mini"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Bus configuration
    BUS_AVG_SPEED_KMH: float = 20.0
    MAX_DIRECT_RESULTS: int = 15
    MAX_TRANSFER_RESULTS: int = 5


settings = Settings()
