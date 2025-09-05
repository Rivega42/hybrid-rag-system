"""Конфигурация системы Hybrid RAG."""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Settings(BaseSettings):
    """Основные настройки системы."""
    
    # === Общие настройки ===
    environment: str = Field(default="development", description="Окружение: development, staging, production")
    debug: bool = Field(default=False, description="Режим отладки")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    secret_key: str = Field(default="your-secret-key", description="Секретный ключ для шифрования")
    
    # === API сервер ===
    api_host: str = Field(default="0.0.0.0", description="Хост API сервера")
    api_port: int = Field(default=8000, description="Порт API сервера")
    api_workers: int = Field(default=4, description="Количество воркеров")
    api_reload: bool = Field(default=False, description="Автоперезагрузка сервера")
    cors_origins: List[str] = Field(default=["*"], description="Разрешенные CORS origins")
    
    # === OpenAI настройки ===
    openai_api_key: str = Field(default="", description="OpenAI API ключ")
    openai_org_id: Optional[str] = Field(default=None, description="OpenAI Organization ID")
    openai_model: str = Field(default="gpt-3.5-turbo", description="Модель OpenAI")
    openai_embedding_model: str = Field(default="text-embedding-ada-002", description="Модель для embeddings")
    openai_temperature: float = Field(default=0.7, description="Температура для генерации")
    openai_max_tokens: int = Field(default=2000, description="Максимальное количество токенов")
    
    # === Anthropic настройки (опционально) ===
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API ключ")
    anthropic_model: str = Field(default="claude-3-opus-20240229", description="Модель Anthropic")
    
    # === Qdrant настройки ===
    qdrant_host: str = Field(default="localhost", description="Хост Qdrant")
    qdrant_port: int = Field(default=6333, description="Порт Qdrant")
    qdrant_api_key: Optional[str] = Field(default=None, description="API ключ Qdrant")
    qdrant_collection_name: str = Field(default="hybrid_rag", description="Название коллекции")
    qdrant_vector_size: int = Field(default=1536, description="Размер векторов")
    
    # === PostgreSQL настройки ===
    postgres_host: str = Field(default="localhost", description="Хост PostgreSQL")
    postgres_port: int = Field(default=5432, description="Порт PostgreSQL")
    postgres_db: str = Field(default="hybrid_rag", description="База данных")
    postgres_user: str = Field(default="hybrid_rag", description="Пользователь БД")
    postgres_password: str = Field(default="password", description="Пароль БД")
    
    # === Redis настройки ===
    redis_host: str = Field(default="localhost", description="Хост Redis")
    redis_port: int = Field(default=6379, description="Порт Redis")
    redis_password: Optional[str] = Field(default=None, description="Пароль Redis")
    redis_db: int = Field(default=0, description="Номер БД Redis")
    cache_ttl: int = Field(default=3600, description="TTL кэша в секундах")
    
    # === n8n интеграция ===
    n8n_webhook_url: Optional[str] = Field(default=None, description="URL n8n webhook")
    n8n_api_key: Optional[str] = Field(default=None, description="API ключ n8n")
    
    # === Стратегии маршрутизации ===
    complexity_threshold_simple: float = Field(default=0.3, description="Порог для простых запросов")
    complexity_threshold_complex: float = Field(default=0.7, description="Порог для сложных запросов")
    max_iterations_agentic: int = Field(default=5, description="Макс итераций для Agentic RAG")
    timeout_seconds: int = Field(default=30, description="Таймаут для запросов")
    
    # === Мониторинг ===
    enable_monitoring: bool = Field(default=True, description="Включить мониторинг")
    prometheus_port: int = Field(default=9090, description="Порт Prometheus")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """Формирует URL для подключения к PostgreSQL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Формирует URL для подключения к Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def qdrant_url(self) -> str:
        """Формирует URL для подключения к Qdrant."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"
    
    def is_production(self) -> bool:
        """Проверяет, является ли окружение production."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Проверяет, является ли окружение development."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек (Singleton)."""
    return Settings()