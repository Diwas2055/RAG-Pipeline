from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""

    # Celery settings
    celery_broker_url: str = ""
    celery_result_backend: str = ""
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_result_expires: int = 3600

    # RAG settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-ada-002"
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.0
    retrieval_top_k: int = 3

    # API settings
    api_title: str = "RAG Pipeline API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Security settings
    api_keys: str = ""  # Comma-separated list of valid API keys
    enable_auth: bool = False  # Enable API key authentication
    enable_rate_limit: bool = False  # Enable rate limiting

    # Rate limiting settings
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "text"  # text or json

    # Storage settings
    upload_dir: str = "./storage/uploads"
    vectorstore_dir: str = "./storage/vectorstores"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


@lru_cache()
def get_settings() -> Settings:
    return Settings()
