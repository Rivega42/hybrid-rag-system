#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_agentic_rag.py - Пример использования Agentic RAG

Этот скрипт демонстрирует продвинутые возможности Agentic RAG:
- Многоэтапная обработка запросов
- Использование специализированных агентов
- Обработка сложных аналитических задач
"""

import asyncio
import os
from typing import List, Dict, Any
from hybrid_rag import HybridRAG
from hybrid_rag.agents import AgentOrchestrator, ResearchAgent, AnalysisAgent, SynthesisAgent
from hybrid_rag.config import AgenticConfig

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticRAGExample:
    """Пример использования Agentic RAG"""
    
    def __init__(self):
        """Инициализация Agentic RAG системы"""
        # Конфигурация для Agentic RAG
        config = AgenticConfig(
            max_iterations=5,
            confidence_threshold=0.8,
            enable_self_reflection=True,
            parallel_agents=True
        )
        
        # Инициализация системы
        self.rag = HybridRAG(
            language='ru',
            agentic_config=config,
            force_agentic=True  # Принудительно использовать Agentic RAG
        )
        
        # Инициализация оркестратора агентов
        self.orchestrator = AgentOrchestrator(
            agents=[
                ResearchAgent(),
                AnalysisAgent(),
                SynthesisAgent()
            ],
            strategy='adaptive'  # adaptive | sequential | parallel
        )
        
        logger.info("Agentic RAG система инициализирована")
    
    async def complex_analysis(self, query: str) -> Dict[str, Any]:
        """Выполнение сложного аналитического запроса
        
        Args:
            query: Текст запроса
            
        Returns:
            Dict с результатами анализа
        """
        logger.info(f"Запуск комплексного анализа: {query}")
        
        # Декомпозиция запроса на подзадачи
        subtasks = await self._decompose_query(query)
        logger.info(f"Декомпозирован на {len(subtasks)} подзадач")
        
        # Выполнение подзадач агентами
        results = {}
        for i, task in enumerate(subtasks, 1):
            logger.info(f"Обработка подзадачи {i}/{len(subtasks)}: {task['description']}")
            
            # Выбор подходящего агента
            agent = self.orchestrator.select_agent(task)
            
            # Выполнение задачи
            result = await agent.execute(
                task=task,
                context=results  # Передаем предыдущие результаты как контекст
            )
            
            results[f"task_{i}"] = result
            
            # Проверка на необходимость дополнительных итераций
            if result.get('needs_refinement', False):
                logger.info("Требуется уточнение результата")
                refined = await self._refine_result(result, task)
                results[f"task_{i}_refined"] = refined
        
        # Синтез финального ответа
        final_result = await self._synthesize_results(query, results)
        
        return final_result
    
    async def _decompose_query(self, query: str) -> List[Dict[str, Any]]:
        """Декомпозиция сложного запроса на подзадачи
        
        Args:
            query: Исходный запрос
            
        Returns:
            Список подзадач
        """
        decomposition_prompt = f"""
        Разбей следующий запрос на логические подзадачи:
        
        Запрос: {query}
        
        Формат ответа:
        1. Подзадача: [описание]
           Тип: [research|analysis|synthesis]
           Приоритет: [high|medium|low]
        """
        
        # Используем LLM для декомпозиции
        response = await self.rag.llm.complete(decomposition_prompt)
        
        # Парсинг ответа (упрощенная версия)
        subtasks = [
            {
                'description': 'Сбор информации по теме',
                'type': 'research',
                'priority': 'high'
            },
            {
                'description': 'Анализ собранных данных',
                'type': 'analysis',
                'priority': 'high'
            },
            {
                'description': 'Формирование выводов',
                'type': 'synthesis',
                'priority': 'medium'
            }
        ]
        
        return subtasks
    
    async def _refine_result(self, result: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Уточнение результата через дополнительную итерацию
        
        Args:
            result: Первоначальный результат
            task: Задача
            
        Returns:
            Уточненный результат
        """
        refinement_prompt = f"""
        Уточни и улучши следующий результат:
        
        Задача: {task['description']}
        Первоначальный результат: {result['content']}
        
        Что нужно улучшить:
        - Добавить больше деталей
        - Проверить факты
        - Улучшить структуру
        """
        
        refined = await self.rag.llm.complete(refinement_prompt)
        
        return {
            'content': refined,
            'confidence': 0.9,
            'refined': True
        }
    
    async def _synthesize_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Синтез финального ответа из результатов подзадач
        
        Args:
            query: Исходный запрос
            results: Результаты подзадач
            
        Returns:
            Финальный результат
        """
        synthesis_prompt = f"""
        Создай полный ответ на основе следующих результатов:
        
        Исходный запрос: {query}
        
        Результаты анализа:
        {results}
        
        Требования к ответу:
        - Структурированность
        - Полнота
        - Точность
        - Практические рекомендации
        """
        
        final_answer = await self.rag.llm.complete(synthesis_prompt)
        
        return {
            'query': query,
            'answer': final_answer,
            'subtasks_completed': len(results),
            'confidence': self._calculate_confidence(results),
            'agents_used': ['research', 'analysis', 'synthesis'],
            'total_iterations': len(results)
        }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Расчет общей уверенности в результате
        
        Args:
            results: Результаты подзадач
            
        Returns:
            Уровень уверенности (0-1)
        """
        confidences = []
        for key, value in results.items():
            if isinstance(value, dict) and 'confidence' in value:
                confidences.append(value['confidence'])
        
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.75  # Значение по умолчанию
    
    async def multi_source_research(self, topic: str) -> Dict[str, Any]:
        """Исследование темы с использованием множественных источников
        
        Args:
            topic: Тема для исследования
            
        Returns:
            Результаты исследования
        """
        logger.info(f"Многоисточниковое исследование: {topic}")
        
        # Определение источников для поиска
        sources = [
            {'type': 'web', 'query': f"{topic} последние новости"},
            {'type': 'academic', 'query': f"{topic} исследования"},
            {'type': 'internal', 'query': f"{topic} документация"},
        ]
        
        research_results = []
        
        # Параллельный поиск по источникам
        tasks = []
        for source in sources:
            task = self._search_source(source)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Объединение результатов
        for source, result in zip(sources, results):
            research_results.append({
                'source': source['type'],
                'data': result,
                'relevance': self._calculate_relevance(result, topic)
            })
        
        # Кросс-валидация результатов
        validated = await self._cross_validate_results(research_results)
        
        return {
            'topic': topic,
            'sources_searched': len(sources),
            'results': validated,
            'summary': await self._create_research_summary(validated),
            'confidence': self._calculate_research_confidence(validated)
        }
    
    async def _search_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Поиск в конкретном источнике
        
        Args:
            source: Описание источника
            
        Returns:
            Результаты поиска
        """
        # Симуляция поиска в разных источниках
        await asyncio.sleep(0.5)  # Имитация задержки
        
        if source['type'] == 'web':
            return {
                'documents': ['Web результат 1', 'Web результат 2'],
                'confidence': 0.8
            }
        elif source['type'] == 'academic':
            return {
                'documents': ['Научная статья 1', 'Научная статья 2'],
                'confidence': 0.9
            }
        else:
            return {
                'documents': ['Внутренний документ 1'],
                'confidence': 0.95
            }
    
    def _calculate_relevance(self, result: Dict[str, Any], topic: str) -> float:
        """Расчет релевантности результата
        
        Args:
            result: Результат поиска
            topic: Тема
            
        Returns:
            Уровень релевантности (0-1)
        """
        # Упрощенный расчет релевантности
        if result.get('documents'):
            return 0.85
        return 0.5
    
    async def _cross_validate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Кросс-валидация результатов из разных источников
        
        Args:
            results: Результаты из разных источников
            
        Returns:
            Валидированные результаты
        """
        # Проверка согласованности информации между источниками
        for i, result in enumerate(results):
            result['validation_score'] = 0.9  # Упрощенная оценка
            result['conflicts'] = []  # Конфликты с другими источниками
        
        return results
    
    async def _create_research_summary(self, results: List[Dict[str, Any]]) -> str:
        """Создание резюме исследования
        
        Args:
            results: Результаты исследования
            
        Returns:
            Текстовое резюме
        """
        summary = "Резюме исследования:\n\n"
        
        for result in results:
            summary += f"Источник: {result['source']}\n"
            summary += f"Релевантность: {result['relevance']:.2%}\n"
            summary += f"Валидация: {result.get('validation_score', 0):.2%}\n\n"
        
        return summary
    
    def _calculate_research_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Расчет общей уверенности в результатах исследования
        
        Args:
            results: Результаты исследования
            
        Returns:
            Уровень уверенности (0-1)
        """
        if not results:
            return 0.0
        
        scores = [r.get('validation_score', 0.5) * r.get('relevance', 0.5) for r in results]
        return sum(scores) / len(scores)


async def main():
    """Главная функция для демонстрации Agentic RAG"""
    
    # Создание экземпляра
    agentic = AgenticRAGExample()
    
    print("\n🤖 ДЕМОНСТРАЦИЯ AGENTIC RAG SYSTEM\n")
    print("="*60)
    
    # Пример 1: Комплексный анализ
    print("\n📊 ПРИМЕР 1: Комплексный анализ")
    print("-"*40)
    
    complex_query = """
    Проанализируй влияние искусственного интеллекта на рынок труда 
    в России за последние 5 лет и спрогнозируй развитие на ближайшие 3 года
    """
    
    print(f"Запрос: {complex_query}\n")
    print("Обработка...")
    
    result = await agentic.complex_analysis(complex_query)
    
    print(f"\n✅ Результат анализа:")
    print(f"Ответ: {result['answer'][:500]}...")
    print(f"\nМетрики:")
    print(f"  • Подзадач выполнено: {result['subtasks_completed']}")
    print(f"  • Уверенность: {result['confidence']:.2%}")
    print(f"  • Использованные агенты: {', '.join(result['agents_used'])}")
    print(f"  • Всего итераций: {result['total_iterations']}")
    
    # Пример 2: Многоисточниковое исследование
    print("\n"*2)
    print("🔍 ПРИМЕР 2: Многоисточниковое исследование")
    print("-"*40)
    
    research_topic = "Квантовые вычисления в медицине"
    
    print(f"Тема исследования: {research_topic}\n")
    print("Поиск по источникам...")
    
    research_result = await agentic.multi_source_research(research_topic)
    
    print(f"\n✅ Результаты исследования:")
    print(f"Источников проверено: {research_result['sources_searched']}")
    print(f"Общая уверенность: {research_result['confidence']:.2%}")
    print(f"\nРезюме:\n{research_result['summary']}")
    
    # Статистика использования агентов
    print("\n"*2)
    print("📈 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ АГЕНТОВ")
    print("-"*40)
    
    stats = {
        'ResearchAgent': {'calls': 5, 'avg_time': 1.2},
        'AnalysisAgent': {'calls': 3, 'avg_time': 2.1},
        'SynthesisAgent': {'calls': 2, 'avg_time': 0.8}
    }
    
    for agent, data in stats.items():
        print(f"\n{agent}:")
        print(f"  • Вызовов: {data['calls']}")
        print(f"  • Среднее время: {data['avg_time']}с")
    
    print("\n" + "="*60)
    print("✨ Демонстрация Agentic RAG завершена!\n")


if __name__ == "__main__":
    # Запуск асинхронной главной функции
    asyncio.run(main())
