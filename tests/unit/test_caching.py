#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_caching.py - Unit тесты для системы кэширования

Тестирует:
- L1 кэш (точные совпадения)
- L2 кэш (семантическое сходство)
- L3 кэш (пути поиска)
- Инвалидация кэша
- TTL механизмы
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from hybrid_rag.caching import CacheManager, L1Cache, L2Cache, L3Cache
from hybrid_rag.exceptions import CacheError


class TestL1Cache:
    """Тесты для L1 кэша (точные совпадения)"""
    
    @pytest.fixture
    def l1_cache(self):
        """Создание экземпляра L1 кэша"""
        return L1Cache(
            max_size=100,
            ttl=3600,
            storage='memory'
        )
    
    @pytest.mark.asyncio
    async def test_exact_match_hit(self, l1_cache):
        """Тест попадания в кэш при точном совпадении"""
        query = "What is Python?"
        result = "Python is a programming language"
        
        # Сохраняем в кэш
        await l1_cache.set(query, result)
        
        # Проверяем попадание
        cached = await l1_cache.get(query)
        assert cached == result
    
    @pytest.mark.asyncio
    async def test_exact_match_miss(self, l1_cache):
        """Тест промаха кэша при отсутствии точного совпадения"""
        await l1_cache.set("What is Python?", "Result")
        
        # Даже небольшое изменение должно привести к промаху
        cached = await l1_cache.get("What is python?")  # lowercase
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, l1_cache):
        """Тест истечения TTL"""
        l1_cache.ttl = 0.1  # 100ms TTL для теста
        
        await l1_cache.set("query", "result")
        assert await l1_cache.get("query") == "result"
        
        # Ждем истечения TTL
        await asyncio.sleep(0.15)
        assert await l1_cache.get("query") is None
    
    @pytest.mark.asyncio
    async def test_max_size_eviction(self, l1_cache):
        """Тест вытеснения при достижении максимального размера"""
        l1_cache.max_size = 3
        
        # Заполняем кэш
        await l1_cache.set("query1", "result1")
        await l1_cache.set("query2", "result2")
        await l1_cache.set("query3", "result3")
        
        # Добавление нового элемента должно вытеснить старый
        await l1_cache.set("query4", "result4")
        
        # Первый элемент должен быть вытеснен (LRU)
        assert await l1_cache.get("query1") is None
        assert await l1_cache.get("query4") == "result4"
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, l1_cache):
        """Тест очистки кэша"""
        await l1_cache.set("query1", "result1")
        await l1_cache.set("query2", "result2")
        
        await l1_cache.clear()
        
        assert await l1_cache.get("query1") is None
        assert await l1_cache.get("query2") is None
        assert l1_cache.size() == 0


class TestL2Cache:
    """Тесты для L2 кэша (семантическое сходство)"""
    
    @pytest.fixture
    def l2_cache(self):
        """Создание экземпляра L2 кэша"""
        return L2Cache(
            similarity_threshold=0.95,
            max_size=500,
            ttl=7200,
            embedding_model=Mock()
        )
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_hit(self, l2_cache):
        """Тест попадания в кэш при семантическом сходстве"""
        # Мокаем embeddings
        embedding1 = np.array([0.1, 0.2, 0.3])
        embedding2 = np.array([0.11, 0.21, 0.31])  # Очень похожий вектор
        
        with patch.object(l2_cache.embedding_model, 'encode') as mock_encode:
            mock_encode.side_effect = [embedding1, embedding1, embedding2]
            
            # Сохраняем первый запрос
            await l2_cache.set("What is Python?", "Result", embedding1)
            
            # Проверяем похожий запрос
            cached = await l2_cache.get_similar("What's Python?", embedding2)
            assert cached is not None
            assert cached['result'] == "Result"
            assert cached['similarity'] > 0.95
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_miss(self, l2_cache):
        """Тест промаха при недостаточном сходстве"""
        embedding1 = np.array([0.1, 0.2, 0.3])
        embedding2 = np.array([0.9, 0.8, 0.7])  # Совсем другой вектор
        
        await l2_cache.set("What is Python?", "Result", embedding1)
        
        cached = await l2_cache.get_similar("What is Java?", embedding2)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_multiple_similar_results(self, l2_cache):
        """Тест получения множественных похожих результатов"""
        # Добавляем несколько похожих запросов
        base_embedding = np.array([0.5, 0.5, 0.5])
        
        for i in range(5):
            embedding = base_embedding + np.random.normal(0, 0.01, 3)
            await l2_cache.set(f"Query {i}", f"Result {i}", embedding)
        
        # Ищем похожие
        similar = await l2_cache.get_top_k_similar(
            "Test query",
            base_embedding,
            k=3
        )
        
        assert len(similar) <= 3
        assert all(s['similarity'] >= l2_cache.similarity_threshold for s in similar)


class TestL3Cache:
    """Тесты для L3 кэша (пути поиска)"""
    
    @pytest.fixture
    def l3_cache(self):
        """Создание экземпляра L3 кэша"""
        return L3Cache(
            max_paths=100,
            ttl=86400
        )
    
    @pytest.mark.asyncio
    async def test_path_caching(self, l3_cache):
        """Тест кэширования путей поиска"""
        query = "Complex analytical query"
        path = [
            {'agent': 'research', 'action': 'search', 'result': 'data1'},
            {'agent': 'analysis', 'action': 'process', 'result': 'data2'},
            {'agent': 'synthesis', 'action': 'combine', 'result': 'final'}
        ]
        
        # Сохраняем путь
        await l3_cache.save_path(query, path)
        
        # Получаем путь
        cached_path = await l3_cache.get_path(query)
        assert cached_path == path
    
    @pytest.mark.asyncio
    async def test_path_optimization(self, l3_cache):
        """Тест оптимизации путей поиска"""
        query = "Query"
        
        # Сохраняем несколько путей для одного запроса
        path1 = [{'steps': 5, 'time': 10.0}]
        path2 = [{'steps': 3, 'time': 5.0}]  # Более оптимальный путь
        
        await l3_cache.save_path(query, path1)
        await l3_cache.save_path(query, path2, is_better=True)
        
        # Должен вернуть более оптимальный путь
        best_path = await l3_cache.get_path(query)
        assert best_path == path2


class TestCacheManager:
    """Тесты для менеджера кэширования"""
    
    @pytest.fixture
    def cache_manager(self):
        """Создание экземпляра менеджера кэша"""
        return CacheManager(
            enable_l1=True,
            enable_l2=True,
            enable_l3=True
        )
    
    @pytest.mark.asyncio
    async def test_multilevel_caching(self, cache_manager):
        """Тест многоуровневого кэширования"""
        query = "Test query"
        result = "Test result"
        
        # Сохраняем результат
        await cache_manager.cache_result(
            query=query,
            result=result,
            strategy='agentic_rag',
            path=[{'step': 1}]
        )
        
        # Проверяем попадание на разных уровнях
        l1_hit = await cache_manager.check_l1(query)
        assert l1_hit is not None
        
        # Проверяем статистику
        stats = cache_manager.get_stats()
        assert stats['l1_hits'] >= 0
        assert stats['l2_hits'] >= 0
        assert stats['l3_hits'] >= 0
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_manager):
        """Тест инвалидации кэша"""
        query = "Test query"
        
        await cache_manager.cache_result(query, "Old result")
        
        # Инвалидация по паттерну
        await cache_manager.invalidate_pattern("Test*")
        
        # Кэш должен быть пустым
        result = await cache_manager.get_cached_result(query)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_warming(self, cache_manager):
        """Тест прогрева кэша"""
        popular_queries = [
            "What is AI?",
            "How does machine learning work?",
            "Python tutorial"
        ]
        
        # Прогрев кэша
        await cache_manager.warm_cache(popular_queries)
        
        # Проверяем что запросы в кэше
        for query in popular_queries:
            assert await cache_manager.check_l1(query) is not None
