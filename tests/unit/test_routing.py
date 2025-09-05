#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_routing.py - Unit тесты для системы маршрутизации запросов

Тестирует:
- Классификацию запросов по сложности
- Выбор оптимальной стратегии обработки
- Fallback механизмы
- Обработку edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from hybrid_rag.routing import QueryRouter, QueryComplexity, RoutingStrategy
from hybrid_rag.exceptions import RoutingError


class TestQueryRouter:
    """Тесты для QueryRouter"""
    
    @pytest.fixture
    def router(self):
        """Создание экземпляра роутера для тестов"""
        return QueryRouter(
            classifier_model='mock',
            threshold_simple=0.3,
            threshold_complex=0.7
        )
    
    @pytest.mark.asyncio
    async def test_simple_query_classification(self, router):
        """Тест классификации простого запроса"""
        # Простые запросы
        simple_queries = [
            "Что такое Python?",
            "Какая столица России?",
            "Определение машинного обучения"
        ]
        
        for query in simple_queries:
            complexity = await router.classify_query(query)
            assert complexity == QueryComplexity.SIMPLE, f"Query '{query}' should be SIMPLE"
    
    @pytest.mark.asyncio
    async def test_complex_query_classification(self, router):
        """Тест классификации сложного запроса"""
        complex_queries = [
            "Проанализируй влияние AI на экономику и предложи стратегию адаптации",
            "Сравни производительность всех версий Python за последние 10 лет",
            "Исследуй корреляцию между климатом и экономическим ростом"
        ]
        
        for query in complex_queries:
            with patch.object(router.classifier, 'predict', return_value=0.9):
                complexity = await router.classify_query(query)
                assert complexity == QueryComplexity.COMPLEX, f"Query '{query}' should be COMPLEX"
    
    @pytest.mark.asyncio
    async def test_medium_query_classification(self, router):
        """Тест классификации запроса средней сложности"""
        medium_queries = [
            "Сравни Python и JavaScript",
            "Найди преимущества облачных технологий",
            "Объясни разницу между ML и DL"
        ]
        
        for query in medium_queries:
            with patch.object(router.classifier, 'predict', return_value=0.5):
                complexity = await router.classify_query(query)
                assert complexity == QueryComplexity.MEDIUM, f"Query '{query}' should be MEDIUM"
    
    @pytest.mark.asyncio
    async def test_routing_strategy_selection(self, router):
        """Тест выбора стратегии маршрутизации"""
        # Маппинг сложности на стратегию
        test_cases = [
            (QueryComplexity.SIMPLE, RoutingStrategy.CLASSIC_RAG),
            (QueryComplexity.MEDIUM, RoutingStrategy.ENHANCED_RAG),
            (QueryComplexity.COMPLEX, RoutingStrategy.AGENTIC_RAG)
        ]
        
        for complexity, expected_strategy in test_cases:
            strategy = router.select_strategy(complexity)
            assert strategy == expected_strategy
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, router):
        """Тест fallback механизма при сбое основной стратегии"""
        query = "Test query"
        
        # Симулируем сбой Agentic RAG
        with patch.object(router, 'execute_agentic_rag', side_effect=Exception("Agentic failed")):
            with patch.object(router, 'execute_enhanced_rag', return_value="Enhanced result"):
                result = await router.route_query(query, enable_fallback=True)
                assert result == "Enhanced result"
    
    @pytest.mark.asyncio
    async def test_cascading_fallback(self, router):
        """Тест каскадного fallback при множественных сбоях"""
        query = "Test query"
        
        # Симулируем сбой Agentic и Enhanced RAG
        with patch.object(router, 'execute_agentic_rag', side_effect=Exception()):
            with patch.object(router, 'execute_enhanced_rag', side_effect=Exception()):
                with patch.object(router, 'execute_classic_rag', return_value="Classic result"):
                    result = await router.route_query(query, enable_fallback=True)
                    assert result == "Classic result"
    
    @pytest.mark.asyncio
    async def test_no_fallback_raises_error(self, router):
        """Тест что без fallback возникает ошибка при сбое"""
        query = "Test query"
        
        with patch.object(router, 'classify_query', return_value=QueryComplexity.COMPLEX):
            with patch.object(router, 'execute_agentic_rag', side_effect=RoutingError("Failed")):
                with pytest.raises(RoutingError):
                    await router.route_query(query, enable_fallback=False)
    
    @pytest.mark.asyncio
    async def test_query_timeout(self, router):
        """Тест таймаута при обработке запроса"""
        query = "Slow query"
        
        async def slow_execution():
            await asyncio.sleep(10)  # Долгая операция
            return "Result"
        
        with patch.object(router, 'execute_agentic_rag', side_effect=slow_execution):
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    router.route_query(query),
                    timeout=0.1
                )
    
    def test_confidence_threshold_adjustment(self, router):
        """Тест динамической настройки порогов уверенности"""
        # Начальные пороги
        assert router.threshold_simple == 0.3
        assert router.threshold_complex == 0.7
        
        # Обновление порогов
        router.update_thresholds(simple=0.2, complex=0.8)
        assert router.threshold_simple == 0.2
        assert router.threshold_complex == 0.8
    
    @pytest.mark.asyncio
    async def test_parallel_routing(self, router):
        """Тест параллельной обработки множественных запросов"""
        queries = [f"Query {i}" for i in range(10)]
        
        with patch.object(router, 'route_query', return_value="Result"):
            results = await router.batch_route(queries)
            assert len(results) == 10
            assert all(r == "Result" for r in results)
    
    @pytest.mark.asyncio
    async def test_cycle_detection(self, router):
        """Тест обнаружения циклических запросов"""
        query = "Recursive query"
        
        # Симулируем циклический запрос
        with patch.object(router, 'detect_cycle', return_value=True):
            with pytest.raises(RoutingError, match="Cycle detected"):
                await router.route_query(query)
    
    @pytest.mark.parametrize("query,expected_complexity", [
        ("", QueryComplexity.SIMPLE),  # Пустой запрос
        ("a" * 10000, QueryComplexity.COMPLEX),  # Очень длинный запрос
        ("SELECT * FROM users", QueryComplexity.MEDIUM),  # SQL запрос
        ("🤔❓", QueryComplexity.SIMPLE),  # Эмодзи
    ])
    @pytest.mark.asyncio
    async def test_edge_cases(self, router, query, expected_complexity):
        """Тест обработки граничных случаев"""
        with patch.object(router.classifier, 'predict') as mock_predict:
            # Настраиваем mock для возврата соответствующих значений
            if expected_complexity == QueryComplexity.SIMPLE:
                mock_predict.return_value = 0.2
            elif expected_complexity == QueryComplexity.MEDIUM:
                mock_predict.return_value = 0.5
            else:
                mock_predict.return_value = 0.9
            
            complexity = await router.classify_query(query)
            assert complexity == expected_complexity


class TestRoutingMetrics:
    """Тесты для метрик маршрутизации"""
    
    @pytest.fixture
    def metrics_router(self):
        """Роутер с включенными метриками"""
        return QueryRouter(
            enable_metrics=True,
            metrics_backend='prometheus'
        )
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, metrics_router):
        """Тест сбора метрик маршрутизации"""
        query = "Test query for metrics"
        
        with patch.object(metrics_router, 'execute_classic_rag', return_value="Result"):
            await metrics_router.route_query(query)
            
            # Проверяем что метрики собраны
            metrics = metrics_router.get_metrics()
            assert 'total_queries' in metrics
            assert 'strategy_distribution' in metrics
            assert 'average_latency' in metrics
    
    @pytest.mark.asyncio
    async def test_strategy_distribution(self, metrics_router):
        """Тест распределения стратегий"""
        # Выполняем несколько запросов
        queries = [
            ("Simple query", QueryComplexity.SIMPLE),
            ("Complex query", QueryComplexity.COMPLEX),
            ("Another simple", QueryComplexity.SIMPLE)
        ]
        
        for query, complexity in queries:
            with patch.object(metrics_router, 'classify_query', return_value=complexity):
                with patch.object(metrics_router, 'execute_strategy', return_value="Result"):
                    await metrics_router.route_query(query)
        
        distribution = metrics_router.get_strategy_distribution()
        assert distribution[RoutingStrategy.CLASSIC_RAG] == 2
        assert distribution[RoutingStrategy.AGENTIC_RAG] == 1
