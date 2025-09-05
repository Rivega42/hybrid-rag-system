"""Основной класс Hybrid RAG системы."""

import asyncio
import logging
import time
import uuid
from typing import Optional, Dict, Any, List

from .config import Settings, get_settings
from .models import (
    QueryResult,
    QueryMetadata,
    RoutingDecision,
    QueryComplexity,
    RoutingStrategy,
    Document
)
from ..routing.router import IntelligentRouter
from ..classic_rag.pipeline import ClassicRAGPipeline
from ..agents.orchestrator import AgentOrchestrator
from ..caching.multi_level import MultiLevelCache
from ..monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


class HybridRAG:
    """Главный класс гибридной RAG системы.
    
    Объединяет классический и агентный подходы для оптимального
    баланса между скоростью, стоимостью и качеством ответов.
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        language: str = "ru",
        cache_enabled: bool = True,
        monitoring_enabled: bool = True,
        use_classic_for_simple: bool = True,
        use_agentic_for_complex: bool = True,
    ):
        """Инициализация Hybrid RAG системы.
        
        Args:
            settings: Настройки системы (если None, используются defaults)
            language: Язык по умолчанию ("ru", "en")
            cache_enabled: Включить кэширование
            monitoring_enabled: Включить мониторинг
            use_classic_for_simple: Использовать Classic RAG для простых запросов
            use_agentic_for_complex: Использовать Agentic RAG для сложных запросов
        """
        self.settings = settings or get_settings()
        self.language = language
        self.cache_enabled = cache_enabled
        self.monitoring_enabled = monitoring_enabled
        self.use_classic_for_simple = use_classic_for_simple
        self.use_agentic_for_complex = use_agentic_for_complex
        
        # Инициализация компонентов
        self._initialize_components()
        
        logger.info("Hybrid RAG система инициализирована")
    
    def _initialize_components(self):
        """Инициализация всех компонентов системы."""
        # Роутер для выбора стратегии
        self.router = IntelligentRouter(self.settings)
        
        # Classic RAG pipeline
        self.classic_rag = ClassicRAGPipeline(self.settings)
        
        # Agentic RAG orchestrator
        self.agent_orchestrator = AgentOrchestrator(self.settings)
        
        # Многоуровневый кэш
        if self.cache_enabled:
            self.cache = MultiLevelCache(self.settings)
        else:
            self.cache = None
        
        # Сборщик метрик
        if self.monitoring_enabled:
            self.metrics = MetricsCollector(self.settings)
        else:
            self.metrics = None
    
    async def query(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force_strategy: Optional[RoutingStrategy] = None,
    ) -> QueryResult:
        """Обработка запроса пользователя.
        
        Args:
            query: Текст запроса
            user_id: ID пользователя (опционально)
            session_id: ID сессии (опционально)
            metadata: Дополнительные метаданные
            force_strategy: Принудительная стратегия (для тестирования)
        
        Returns:
            QueryResult: Результат обработки запроса
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())
        
        logger.info(f"Обработка запроса {query_id}: {query[:100]}...")
        
        try:
            # Анализ запроса
            query_metadata = await self._analyze_query(
                query, query_id, user_id, session_id
            )
            
            # Проверка кэша
            if self.cache_enabled and not force_strategy:
                cached_result = await self._check_cache(query_metadata)
                if cached_result:
                    logger.info(f"Найден результат в кэше для {query_id}")
                    return cached_result
            
            # Выбор стратегии маршрутизации
            routing_decision = await self._route_query(
                query_metadata, force_strategy
            )
            
            # Выполнение запроса согласно стратегии
            result = await self._execute_query(
                query_metadata, routing_decision
            )
            
            # Сохранение в кэш
            if self.cache_enabled:
                await self._save_to_cache(query_metadata, result)
            
            # Сбор метрик
            if self.monitoring_enabled:
                await self._collect_metrics(result)
            
            # Добавление финальной информации
            result.latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Запрос {query_id} обработан за {result.latency_ms}ms "
                f"используя стратегию {result.strategy_used}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса {query_id}: {str(e)}")
            return self._create_error_result(
                query_id, query_metadata, str(e), 
                int((time.time() - start_time) * 1000)
            )
    
    async def _analyze_query(
        self,
        query: str,
        query_id: str,
        user_id: Optional[str],
        session_id: Optional[str],
    ) -> QueryMetadata:
        """Анализ входящего запроса.
        
        Args:
            query: Текст запроса
            query_id: ID запроса
            user_id: ID пользователя
            session_id: ID сессии
        
        Returns:
            QueryMetadata: Метаданные анализа запроса
        """
        # Здесь будет логика анализа запроса
        # Пока используем заглушку
        
        # Оценка сложности (временная логика)
        complexity_score = len(query.split()) / 50.0  # Простая эвристика
        complexity_score = min(1.0, complexity_score)
        
        if complexity_score < 0.3:
            complexity = QueryComplexity.SIMPLE
        elif complexity_score < 0.6:
            complexity = QueryComplexity.MODERATE
        elif complexity_score < 0.8:
            complexity = QueryComplexity.COMPLEX
        else:
            complexity = QueryComplexity.MULTI_HOP
        
        return QueryMetadata(
            query_id=query_id,
            original_query=query,
            language=self.language,
            complexity=complexity,
            complexity_score=complexity_score,
            entities=[],  # TODO: Извлечение сущностей
            intent="general",  # TODO: Определение интента
            keywords=[],  # TODO: Извлечение ключевых слов
            user_id=user_id,
            session_id=session_id,
        )
    
    async def _check_cache(
        self,
        query_metadata: QueryMetadata
    ) -> Optional[QueryResult]:
        """Проверка кэша на наличие результата.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            QueryResult если найден в кэше, иначе None
        """
        if not self.cache:
            return None
        
        cached = await self.cache.get(
            key=query_metadata.original_query,
            embedding=query_metadata.embedding
        )
        
        if cached:
            # Преобразуем кэшированный результат в QueryResult
            result = QueryResult(**cached)
            result.cached = True
            return result
        
        return None
    
    async def _route_query(
        self,
        query_metadata: QueryMetadata,
        force_strategy: Optional[RoutingStrategy] = None,
    ) -> RoutingDecision:
        """Определение стратегии маршрутизации.
        
        Args:
            query_metadata: Метаданные запроса
            force_strategy: Принудительная стратегия
        
        Returns:
            RoutingDecision: Решение о маршрутизации
        """
        if force_strategy:
            return RoutingDecision(
                strategy=force_strategy,
                confidence=1.0,
                reasoning="Принудительная стратегия",
                fallback_strategies=[],
                estimated_time_ms=1000,
                estimated_cost_usd=0.001,
            )
        
        return await self.router.route(query_metadata)
    
    async def _execute_query(
        self,
        query_metadata: QueryMetadata,
        routing_decision: RoutingDecision,
    ) -> QueryResult:
        """Выполнение запроса согласно выбранной стратегии.
        
        Args:
            query_metadata: Метаданные запроса
            routing_decision: Решение о маршрутизации
        
        Returns:
            QueryResult: Результат выполнения
        """
        strategy = routing_decision.strategy
        
        if strategy == RoutingStrategy.CLASSIC_RAG:
            return await self._execute_classic_rag(query_metadata)
        elif strategy == RoutingStrategy.AGENTIC_RAG:
            return await self._execute_agentic_rag(query_metadata)
        elif strategy == RoutingStrategy.HYBRID:
            return await self._execute_hybrid(query_metadata)
        else:
            raise ValueError(f"Неизвестная стратегия: {strategy}")
    
    async def _execute_classic_rag(
        self,
        query_metadata: QueryMetadata
    ) -> QueryResult:
        """Выполнение через Classic RAG pipeline.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            QueryResult: Результат выполнения
        """
        start_time = time.time()
        
        # Выполняем классический RAG
        result = await self.classic_rag.process(query_metadata)
        
        # Формируем финальный результат
        return QueryResult(
            query_id=query_metadata.query_id,
            answer=result["answer"],
            strategy_used=RoutingStrategy.CLASSIC_RAG,
            confidence_score=result.get("confidence", 0.8),
            relevance_score=result.get("relevance", 0.8),
            latency_ms=int((time.time() - start_time) * 1000),
            tokens_used=result.get("tokens_used", 0),
            cost_usd=result.get("cost", 0.001),
            documents_retrieved=result.get("documents", []),
            agents_used=[],
            agent_results=[],
            execution_path=["classic_rag"],
            reasoning_chain=[],
            metadata=query_metadata,
            cached=False,
            fallback_used=False,
        )
    
    async def _execute_agentic_rag(
        self,
        query_metadata: QueryMetadata
    ) -> QueryResult:
        """Выполнение через Agentic RAG pipeline.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            QueryResult: Результат выполнения
        """
        start_time = time.time()
        
        # Выполняем агентный RAG
        result = await self.agent_orchestrator.orchestrate(query_metadata)
        
        # Формируем финальный результат
        return QueryResult(
            query_id=query_metadata.query_id,
            answer=result["answer"],
            strategy_used=RoutingStrategy.AGENTIC_RAG,
            confidence_score=result.get("confidence", 0.9),
            relevance_score=result.get("relevance", 0.9),
            latency_ms=int((time.time() - start_time) * 1000),
            tokens_used=result.get("tokens_used", 0),
            cost_usd=result.get("cost", 0.01),
            documents_retrieved=result.get("documents", []),
            agents_used=result.get("agents_used", []),
            agent_results=result.get("agent_results", []),
            execution_path=result.get("execution_path", []),
            reasoning_chain=result.get("reasoning_chain", []),
            metadata=query_metadata,
            cached=False,
            fallback_used=False,
        )
    
    async def _execute_hybrid(
        self,
        query_metadata: QueryMetadata
    ) -> QueryResult:
        """Выполнение через гибридный подход.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            QueryResult: Результат выполнения
        """
        # Запускаем оба pipeline параллельно
        classic_task = asyncio.create_task(
            self._execute_classic_rag(query_metadata)
        )
        agentic_task = asyncio.create_task(
            self._execute_agentic_rag(query_metadata)
        )
        
        # Ждем завершения обоих
        classic_result, agentic_result = await asyncio.gather(
            classic_task, agentic_task
        )
        
        # Объединяем результаты (используем более уверенный)
        if agentic_result.confidence_score > classic_result.confidence_score:
            final_result = agentic_result
        else:
            final_result = classic_result
        
        final_result.strategy_used = RoutingStrategy.HYBRID
        return final_result
    
    async def _save_to_cache(
        self,
        query_metadata: QueryMetadata,
        result: QueryResult
    ):
        """Сохранение результата в кэш.
        
        Args:
            query_metadata: Метаданные запроса
            result: Результат для сохранения
        """
        if not self.cache:
            return
        
        await self.cache.set(
            key=query_metadata.original_query,
            value=result.dict(),
            embedding=query_metadata.embedding,
            execution_path=result.execution_path,
        )
    
    async def _collect_metrics(
        self,
        result: QueryResult
    ):
        """Сбор метрик выполнения.
        
        Args:
            result: Результат выполнения
        """
        if not self.metrics:
            return
        
        await self.metrics.record(
            strategy=result.strategy_used.value,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_used,
            cost_usd=result.cost_usd,
            confidence_score=result.confidence_score,
            relevance_score=result.relevance_score,
            cached=result.cached,
            fallback_used=result.fallback_used,
        )
    
    def _create_error_result(
        self,
        query_id: str,
        query_metadata: Optional[QueryMetadata],
        error: str,
        latency_ms: int,
    ) -> QueryResult:
        """Создание результата с ошибкой.
        
        Args:
            query_id: ID запроса
            query_metadata: Метаданные запроса
            error: Текст ошибки
            latency_ms: Время выполнения
        
        Returns:
            QueryResult: Результат с ошибкой
        """
        return QueryResult(
            query_id=query_id,
            answer="Извините, произошла ошибка при обработке вашего запроса.",
            strategy_used=RoutingStrategy.CLASSIC_RAG,
            confidence_score=0.0,
            relevance_score=0.0,
            latency_ms=latency_ms,
            tokens_used=0,
            cost_usd=0.0,
            documents_retrieved=[],
            agents_used=[],
            agent_results=[],
            execution_path=["error"],
            reasoning_chain=[],
            metadata=query_metadata or QueryMetadata(
                query_id=query_id,
                original_query="",
                language="ru",
                complexity=QueryComplexity.SIMPLE,
                complexity_score=0.0,
                entities=[],
                intent="error",
                keywords=[],
            ),
            cached=False,
            fallback_used=True,
            error=error,
        )
    
    async def complex_query(
        self,
        query: str,
        **kwargs
    ) -> QueryResult:
        """Принудительное использование Agentic RAG для сложных запросов.
        
        Args:
            query: Текст запроса
            **kwargs: Дополнительные параметры
        
        Returns:
            QueryResult: Результат обработки
        """
        return await self.query(
            query,
            force_strategy=RoutingStrategy.AGENTIC_RAG,
            **kwargs
        )
    
    async def simple_query(
        self,
        query: str,
        **kwargs
    ) -> QueryResult:
        """Принудительное использование Classic RAG для простых запросов.
        
        Args:
            query: Текст запроса
            **kwargs: Дополнительные параметры
        
        Returns:
            QueryResult: Результат обработки
        """
        return await self.query(
            query,
            force_strategy=RoutingStrategy.CLASSIC_RAG,
            **kwargs
        )
    
    async def close(self):
        """Закрытие всех соединений и освобождение ресурсов."""
        logger.info("Закрытие Hybrid RAG системы...")
        
        # Закрываем компоненты
        if hasattr(self.classic_rag, 'close'):
            await self.classic_rag.close()
        
        if hasattr(self.agent_orchestrator, 'close'):
            await self.agent_orchestrator.close()
        
        if self.cache and hasattr(self.cache, 'close'):
            await self.cache.close()
        
        if self.metrics and hasattr(self.metrics, 'close'):
            await self.metrics.close()
        
        logger.info("Hybrid RAG система закрыта")
    
    async def __aenter__(self):
        """Async context manager вход."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager выход."""
        await self.close()