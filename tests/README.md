# 🧪 Тесты Hybrid RAG System

## 📋 Структура тестов

```
tests/
├── unit/              # Unit тесты отдельных компонентов
│   ├── test_routing.py
│   ├── test_caching.py
│   ├── test_agents.py
│   └── test_indexing.py
├── integration/       # Интеграционные тесты
│   ├── test_rag_flow.py
│   ├── test_api.py
│   └── test_vector_store.py
├── e2e/              # End-to-end тесты
│   ├── test_full_pipeline.py
│   └── test_production_scenarios.py
├── performance/      # Тесты производительности
│   ├── test_latency.py
│   └── test_throughput.py
└── fixtures/         # Тестовые данные
    ├── documents/
    └── queries.json
```

## 🚀 Запуск тестов

### Все тесты
```bash
pytest
```

### Только unit тесты
```bash
pytest tests/unit/
```

### С покрытием кода
```bash
pytest --cov=hybrid_rag --cov-report=html
```

### Параллельное выполнение
```bash
pytest -n auto
```

## 📊 Метрики качества

- ✅ Покрытие кода: >80%
- ✅ Все тесты проходят
- ✅ Нет flaky тестов
- ✅ Время выполнения: <5 минут

## 🔧 Конфигурация

См. файл `pytest.ini` для настройки pytest.
