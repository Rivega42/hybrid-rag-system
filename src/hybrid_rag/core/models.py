"""Модели данных для Hybrid RAG системы."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import numpy as np


class QueryComplexity(str, Enum):
    """Уровень сложности запроса."""
    SIMPLE = "simple"  # Простой факт-запрос
    MODERATE = "moderate"  # Средняя сложность
    COMPLEX = "complex"  # Сложный многоэтапный
    MULTI_HOP = "multi_hop"  # Многоуровневый с зависимостями


class RoutingStrategy(str, Enum):
    """Стратегия маршрутизации запроса."""
    CLASSIC_RAG = "classic_rag"  # Классический RAG
    AGENTIC_RAG = "agentic_rag"  # Агентный RAG
    HYBRID = "hybrid"  # Гибридный подход
    CACHE = "cache"  # Из кэша


class AgentType(str, Enum):
    """Типы агентов в системе."""
    RESEARCH = "research"  # Исследовательский агент
    ANALYSIS = "analysis"  # Аналитический агент
    SYNTHESIS = "synthesis"  # Синтезирующий агент
    VERIFICATION = "verification"  # Проверяющий агент
    CODE = "code"  # Агент для работы с кодом


class QueryMetadata(BaseModel):
    """Метаданные анализа запроса."""
    
    query_id: str = Field(description="Уникальный ID запроса")
    original_query: str = Field(description="Исходный запрос пользователя")
    language: str = Field(default="ru", description="Язык запроса")
    complexity: QueryComplexity = Field(description="Оценка сложности")
    complexity_score: float = Field(description="Числовая оценка сложности (0-1)")
    entities: List[str] = Field(default_factory=list, description="Извлеченные сущности")
    intent: str = Field(description="Определенное намерение")
    keywords: List[str] = Field(default_factory=list, description="Ключевые слова")
    embedding: Optional[List[float]] = Field(default=None, description="Векторное представление")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время запроса")
    user_id: Optional[str] = Field(default=None, description="ID пользователя")
    session_id: Optional[str] = Field(default=None, description="ID сессии")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            np.ndarray: lambda v: v.tolist()
        }


class RoutingDecision(BaseModel):
    """Решение о маршрутизации запроса."""
    
    strategy: RoutingStrategy = Field(description="Выбранная стратегия")
    confidence: float = Field(description="Уверенность в решении (0-1)")
    reasoning: str = Field(description="Объяснение выбора")
    fallback_strategies: List[RoutingStrategy] = Field(
        default_factory=list,
        description="Запасные стратегии"
    )
    estimated_time_ms: int = Field(description="Ожидаемое время выполнения")
    estimated_cost_usd: float = Field(description="Ожидаемая стоимость")
    cache_hit: bool = Field(default=False, description="Найден в кэше")


class Document(BaseModel):
    """Документ для обработки."""
    
    doc_id: str = Field(description="ID документа")
    content: str = Field(description="Содержимое документа")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    embedding: Optional[List[float]] = Field(default=None, description="Векторное представление")
    score: Optional[float] = Field(default=None, description="Релевантность")
    source: Optional[str] = Field(default=None, description="Источник")
    chunk_id: Optional[int] = Field(default=None, description="ID части документа")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentResult(BaseModel):
    """Результат работы агента."""
    
    agent_type: AgentType = Field(description="Тип агента")
    agent_id: str = Field(description="ID агента")
    result: str = Field(description="Результат работы")
    confidence: float = Field(description="Уверенность (0-1)")
    sources: List[str] = Field(default_factory=list, description="Использованные источники")
    execution_time_ms: int = Field(description="Время выполнения")
    tokens_used: int = Field(description="Использовано токенов")
    cost_usd: float = Field(description="Стоимость")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")


class QueryResult(BaseModel):
    """Финальный результат обработки запроса."""
    
    query_id: str = Field(description="ID запроса")
    answer: str = Field(description="Сгенерированный ответ")
    strategy_used: RoutingStrategy = Field(description="Использованная стратегия")
    confidence_score: float = Field(description="Уверенность в ответе (0-1)")
    relevance_score: float = Field(description="Релевантность ответа (0-1)")
    
    # Метрики производительности
    latency_ms: int = Field(description="Общая задержка в миллисекундах")
    tokens_used: int = Field(description="Всего использовано токенов")
    cost_usd: float = Field(description="Общая стоимость")
    
    # Детали выполнения
    documents_retrieved: List[Document] = Field(
        default_factory=list,
        description="Найденные документы"
    )
    agents_used: List[AgentType] = Field(
        default_factory=list,
        description="Использованные агенты"
    )
    agent_results: List[AgentResult] = Field(
        default_factory=list,
        description="Результаты работы агентов"
    )
    
    # Путь выполнения
    execution_path: List[str] = Field(
        default_factory=list,
        description="Последовательность шагов выполнения"
    )
    reasoning_chain: List[str] = Field(
        default_factory=list,
        description="Цепочка рассуждений"
    )
    
    # Метаданные
    metadata: QueryMetadata = Field(description="Метаданные запроса")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = Field(default=False, description="Был ли ответ из кэша")
    fallback_used: bool = Field(default=False, description="Использован ли fallback")
    error: Optional[str] = Field(default=None, description="Сообщение об ошибке")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheEntry(BaseModel):
    """Запись в кэше."""
    
    key: str = Field(description="Ключ кэша")
    value: Any = Field(description="Значение")
    embedding: Optional[List[float]] = Field(default=None, description="Векторное представление")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="Время истечения")
    hit_count: int = Field(default=0, description="Количество обращений")
    metadata: Dict[str, Any] = Field(default_factory=dict)