"""Классификатор запросов для определения их сложности."""

import logging
import re
from typing import Dict, Any
import numpy as np

from ..core.config import Settings
from ..core.models import QueryMetadata, QueryComplexity

logger = logging.getLogger(__name__)


class QueryClassifier:
    """ML-классификатор для определения сложности и типа запросов."""
    
    def __init__(self, settings: Settings):
        """Инициализация классификатора.
        
        Args:
            settings: Настройки системы
        """
        self.settings = settings
        self.model = None  # TODO: Загрузить обученную модель
        
        # Паттерны для эвристического анализа
        self.simple_patterns = [
            r"что такое",
            r"кто такой",
            r"когда",
            r"где находится",
            r"какая столица",
            r"дай определение",
            r"назови",
            r"перечисли"
        ]
        
        self.complex_patterns = [
            r"проанализируй",
            r"сравни",
            r"оцени влияние",
            r"найди все",
            r"исследуй",
            r"определи взаимосвязь",
            r"сделай прогноз",
            r"разработай стратегию"
        ]
        
        self.multi_hop_keywords = [
            "и", "а также", "кроме того", "учитывая",
            "на основе", "исходя из", "в контексте"
        ]
        
        logger.info("Query Classifier инициализирован")
    
    async def classify(self, query_metadata: QueryMetadata) -> Dict[str, Any]:
        """Классификация запроса.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            Результат классификации с уверенностью
        """
        query = query_metadata.original_query.lower()
        
        # Если есть обученная модель, используем её
        if self.model:
            return await self._ml_classify(query_metadata)
        
        # Иначе используем эвристики
        return self._heuristic_classify(query)
    
    def _heuristic_classify(self, query: str) -> Dict[str, Any]:
        """Эвристическая классификация запроса.
        
        Args:
            query: Текст запроса
        
        Returns:
            Результат классификации
        """
        # Проверяем простые паттерны
        for pattern in self.simple_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return {
                    "complexity": QueryComplexity.SIMPLE,
                    "confidence": 0.85,
                    "features": {
                        "pattern_match": pattern,
                        "query_length": len(query),
                        "word_count": len(query.split())
                    }
                }
        
        # Проверяем сложные паттерны
        for pattern in self.complex_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Проверяем на multi-hop
                multi_hop_count = sum(
                    1 for keyword in self.multi_hop_keywords
                    if keyword in query
                )
                
                if multi_hop_count >= 2:
                    complexity = QueryComplexity.MULTI_HOP
                else:
                    complexity = QueryComplexity.COMPLEX
                
                return {
                    "complexity": complexity,
                    "confidence": 0.75,
                    "features": {
                        "pattern_match": pattern,
                        "multi_hop_indicators": multi_hop_count,
                        "query_length": len(query),
                        "word_count": len(query.split())
                    }
                }
        
        # Анализируем на основе длины и структуры
        word_count = len(query.split())
        question_marks = query.count('?')
        has_enumeration = bool(re.search(r'\d+\.', query))
        
        # Простая эвристика на основе длины
        if word_count < 10:
            complexity = QueryComplexity.SIMPLE
            confidence = 0.7
        elif word_count < 30:
            complexity = QueryComplexity.MODERATE
            confidence = 0.6
        elif word_count < 50:
            complexity = QueryComplexity.COMPLEX
            confidence = 0.6
        else:
            complexity = QueryComplexity.MULTI_HOP
            confidence = 0.7
        
        # Корректировка на основе дополнительных признаков
        if question_marks > 1:
            complexity = QueryComplexity.MULTI_HOP
            confidence *= 0.9
        
        if has_enumeration:
            if complexity == QueryComplexity.SIMPLE:
                complexity = QueryComplexity.MODERATE
            confidence *= 0.95
        
        return {
            "complexity": complexity,
            "confidence": confidence,
            "features": {
                "word_count": word_count,
                "question_marks": question_marks,
                "has_enumeration": has_enumeration,
                "query_length": len(query)
            }
        }
    
    async def _ml_classify(self, query_metadata: QueryMetadata) -> Dict[str, Any]:
        """ML-based классификация запроса.
        
        Args:
            query_metadata: Метаданные запроса
        
        Returns:
            Результат классификации
        """
        # TODO: Реализовать ML классификацию
        # Здесь будет:
        # 1. Извлечение признаков
        # 2. Применение модели
        # 3. Постобработка предсказаний
        
        # Пока возвращаем заглушку
        return self._heuristic_classify(query_metadata.original_query.lower())
    
    def extract_features(self, query: str) -> np.ndarray:
        """Извлечение признаков из запроса для ML модели.
        
        Args:
            query: Текст запроса
        
        Returns:
            Вектор признаков
        """
        features = []
        
        # Базовые статистики
        features.append(len(query))  # Длина запроса
        features.append(len(query.split()))  # Количество слов
        features.append(query.count('?'))  # Количество вопросов
        features.append(query.count(','))  # Количество запятых
        
        # Наличие ключевых слов
        for pattern in self.simple_patterns:
            features.append(
                1.0 if re.search(pattern, query, re.IGNORECASE) else 0.0
            )
        
        for pattern in self.complex_patterns:
            features.append(
                1.0 if re.search(pattern, query, re.IGNORECASE) else 0.0
            )
        
        # Наличие multi-hop индикаторов
        for keyword in self.multi_hop_keywords:
            features.append(1.0 if keyword in query else 0.0)
        
        return np.array(features)
    
    def train(self, training_data: list) -> None:
        """Обучение классификатора на исторических данных.
        
        Args:
            training_data: Список примеров (query, complexity, strategy_success)
        """
        # TODO: Реализовать обучение модели
        # Здесь будет:
        # 1. Подготовка данных
        # 2. Обучение модели (например, XGBoost или CatBoost)
        # 3. Валидация
        # 4. Сохранение модели
        
        logger.info(f"Обучение модели на {len(training_data)} примерах")
    
    def evaluate(self, test_data: list) -> Dict[str, float]:
        """Оценка качества классификатора.
        
        Args:
            test_data: Тестовые данные
        
        Returns:
            Метрики качества
        """
        # TODO: Реализовать оценку модели
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0
        }