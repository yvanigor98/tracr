from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tracr:tracr@localhost:5432/tracr"
    POSTGRES_USER: str = "tracr"
    POSTGRES_PASSWORD: str = "tracr"
    POSTGRES_DB: str = "tracr"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # NLP
    NLP_SERVICE_URL: str = "http://localhost:8001"
    NLP_MODEL: str = "en_core_web_trf"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "tracr-neo4j"

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
