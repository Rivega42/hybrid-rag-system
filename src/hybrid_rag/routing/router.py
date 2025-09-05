"""Интеллектуальный роутер для выбора стратегии обработки запросов."""

import logging
from typing import Optional
import numpy as np

from ..core.config import Settings
from ..core.models import (
    QueryMetadata,
    RoutingDecision,
    RoutingStrategy,
    QueryComplexity
)
from .classifier import QueryClassifier

logger = logging.getLogger(__name__)


class IntelligentRouter:
    """Интеллектуальный маршрутизатор запросов.
    
    Выбирает оптимальную стратегию обработки на основе анализа запроса.
    """
    
    def __init__(self, settings: Settings):
        """Инициализация роутера.
        
        Args:
            settings: Настройки системы
        """
        self.settings = settings
        self.classifier = QueryClassifier(settings)
        
        # Пороги для принятия решений
        self.simple_threshold = settings.complexity_threshold_simple
        self.complex_threshold = settings.complexity_threshold_complex
        
        logger.info("Intelligent Router инициализирован")
    
    async def route(self, query_metadata: QueryMetadata) -> RoutingDecision:
        """Определение маршрута для запроса.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            RoutingDecision: Решение о маршрутизации
        """
        logger.debug(f"Маршрутизация запроса {query_metadata.query_id}")
        
        # Получаем предсказание классификатора
        classification = await self.classifier.classify(query_metadata)
        
        # Определяем стратегию на основе классификации
        strategy = self._determine_strategy(
            query_metadata.complexity,
            classification["confidence"]
        )
        
        # Определяем запасные стратегии
        fallback_strategies = self._get_fallback_strategies(strategy)
        
        # Оцениваем время и стоимость
        estimated_time = self._estimate_time(strategy, query_metadata)
        estimated_cost = self._estimate_cost(strategy, query_metadata)
        
        # Проверяем доступность ресурсов
        strategy = await self._check_resource_availability(strategy)
        
        # Формируем решение
        decision = RoutingDecision(
            strategy=strategy,
            confidence=classification["confidence"],
            reasoning=self._generate_reasoning(strategy, query_metadata),
            fallback_strategies=fallback_strategies,
            estimated_time_ms=estimated_time,
            estimated_cost_usd=estimated_cost,
            cache_hit=False
        )
        
        logger.info(
            f"Запрос {query_metadata.query_id} направлен на {strategy.value} "
            f"(уверенность: {decision.confidence:.2f})"
        )
        
        return decision
    
    def _determine_strategy(
        self,
        complexity: QueryComplexity,
        confidence: float
    ) -> RoutingStrategy:
        """Определение стратегии на основе сложности.
        
        Args:
            complexity: Сложность запроса
            confidence: Уверенность классификатора
        
        Returns:
            RoutingStrategy: Выбранная стратегия
        """
        # Простые запросы -> Classic RAG
        if complexity == QueryComplexity.SIMPLE:
            return RoutingStrategy.CLASSIC_RAG
        
        # Сложные запросы -> Agentic RAG
        elif complexity == QueryComplexity.COMPLEX or complexity == QueryComplexity.MULTI_HOP:
            return RoutingStrategy.AGENTIC_RAG
        
        # Средние запросы -> решение на основе уверенности
        elif complexity == QueryComplexity.MODERATE:
            if confidence > 0.7:
                return RoutingStrategy.CLASSIC_RAG
            else:
                return RoutingStrategy.HYBRID
        
        # По умолчанию - гибридный подход
        return RoutingStrategy.HYBRID
    
    def _get_fallback_strategies(
        self,
        primary_strategy: RoutingStrategy
    ) -> list[RoutingStrategy]:
        """Получение запасных стратегий.
        
        Args:
            primary_strategy: Основная стратегия
        
        Returns:
            Список запасных стратегий
        """
        if primary_strategy == RoutingStrategy.AGENTIC_RAG:
            return [
                RoutingStrategy.HYBRID,
                RoutingStrategy.CLASSIC_RAG
            ]
        elif primary_strategy == RoutingStrategy.HYBRID:
            return [
                RoutingStrategy.CLASSIC_RAG,
                RoutingStrategy.AGENTIC_RAG
            ]
        elif primary_strategy == RoutingStrategy.CLASSIC_RAG:
            return [
                RoutingStrategy.HYBRID,
                RoutingStrategy.AGENTIC_RAG
            ]
        else:
            return [RoutingStrategy.CLASSIC_RAG]
    
    def _estimate_time(
        self,
        strategy: RoutingStrategy,
        query_metadata: QueryMetadata
    ) -> int:
        """Оценка времени выполнения.
        
        Args:
            strategy: Стратегия обработки
            query_metadata: Метаданные запроса
        
        Returns:
            Ожидаемое время в миллисекундах
        """
        base_times = {
            RoutingStrategy.CLASSIC_RAG: 200,
            RoutingStrategy.AGENTIC_RAG: 2000,
            RoutingStrategy.HYBRID: 1500,
            RoutingStrategy.CACHE: 10
        }
        
        base_time = base_times.get(strategy, 1000)
        
        # Корректировка на основе сложности
        complexity_multiplier = {
            QueryComplexity.SIMPLE: 0.5,
            QueryComplexity.MODERATE: 1.0,
            QueryComplexity.COMPLEX: 2.0,
            QueryComplexity.MULTI_HOP: 3.0
        }
        
        multiplier = complexity_multiplier.get(
            query_metadata.complexity, 1.0
        )
        
        return int(base_time * multiplier)
    
    def _estimate_cost(
        self,
        strategy: RoutingStrategy,
        query_metadata: QueryMetadata
    ) -> float:
        """Оценка стоимости выполнения.
        
        Args:
            strategy: Стратегия обработки
            query_metadata: Метаданные запроса
        
        Returns:
            Ожидаемая стоимость в USD
        """
        base_costs = {
            RoutingStrategy.CLASSIC_RAG: 0.001,
            RoutingStrategy.AGENTIC_RAG: 0.01,
            RoutingStrategy.HYBRID: 0.005,
            RoutingStrategy.CACHE: 0.0
        }
        
        base_cost = base_costs.get(strategy, 0.003)
        
        # Корректировка на основе длины запроса
        query_length = len(query_metadata.original_query)
        length_multiplier = 1.0 + (query_length / 1000.0)
        
        return base_cost * length_multiplier
    
    async def _check_resource_availability(
        self,
        strategy: RoutingStrategy
    ) -> RoutingStrategy:
        """Проверка доступности ресурсов для выбранной стратегии.
        
        Args:
            strategy: Предложенная стратегия
        
        Returns:
            RoutingStrategy: Финальная стратегия с учетом доступности
        """
        # TODO: Реализовать проверку доступности ресурсов
        # Например:
        # - Проверка доступности API
        # - Проверка лимитов rate limiting
        # - Проверка доступности агентов
        
        return strategy
    
    def _generate_reasoning(
        self,
        strategy: RoutingStrategy,
        query_metadata: QueryMetadata
    ) -> str:
        """Генерация объяснения выбора стратегии.
        
        Args:
            strategy: Выбранная стратегия
            query_metadata: Метаданные запроса
        
        Returns:
            Текстовое объяснение
        """
        reasoning_templates = {
            RoutingStrategy.CLASSIC_RAG: (
                "Запрос классифицирован как {complexity} сложности. "
                "Использование Classic RAG для быстрого поиска ответа."
            ),
            RoutingStrategy.AGENTIC_RAG: (
                "Запрос требует сложного анализа и многоэтапной обработки. "
                "Использование Agentic RAG для глубокого исследования."
            ),
            RoutingStrategy.HYBRID: (
                "Запрос средней сложности требует сбалансированного подхода. "
                "Использование гибридной стратегии для оптимального результата."
            ),
            RoutingStrategy.CACHE: (
                "Найден похожий запрос в кэше. "
                "Использование закэшированного результата для мгновенного ответа."
            )
        }
        
        template = reasoning_templates.get(
            strategy,
            "Выбрана стратегия {strategy} на основе анализа запроса."
        )
        
        return template.format(
            complexity=query_metadata.complexity.value,
            strategy=strategy.value
        )
    
    def get_statistics(self) -> dict:
        """Получение статистики работы роутера.
        
        Returns:
            Словарь со статистикой
        """
        # TODO: Реализовать сбор статистики
        return {
            "total_requests": 0,
            "strategy_distribution": {
                "classic_rag": 0,
                "agentic_rag": 0,
                "hybrid": 0,
                "cache": 0
            },
            "average_confidence": 0.0,
            "fallback_rate": 0.0
        }