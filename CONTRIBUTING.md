# Руководство по внесению вклада в Hybrid RAG System

Спасибо за интерес к проекту Hybrid RAG System! Мы приветствуем любой вклад в развитие проекта.

## 📋 Содержание

- [Кодекс поведения](#кодекс-поведения)
- [Как я могу помочь?](#как-я-могу-помочь)
- [С чего начать](#с-чего-начать)
- [Процесс разработки](#процесс-разработки)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Создание Pull Request](#создание-pull-request)
- [Сообщение о проблемах](#сообщение-о-проблемах)

## 📜 Кодекс поведения

Все участники проекта обязуются следовать нашему [Кодексу поведения](CODE_OF_CONDUCT.md). Пожалуйста, ознакомьтесь с ним перед участием.

## 🤝 Как я могу помочь?

### Сообщить об ошибке
- Проверьте, что ошибка ещё не была зарегистрирована в [Issues](https://github.com/Rivega42/hybrid-rag-system/issues)
- Создайте новый Issue с подробным описанием проблемы
- Приложите код для воспроизведения ошибки
- Укажите версию системы и окружение

### Предложить новую функцию
- Проверьте [Roadmap](https://hrag.mixbase.ru/roadmap) и существующие Issues
- Создайте Issue с тегом `enhancement`
- Опишите предлагаемую функцию и её ценность
- Будьте готовы к обсуждению и доработке идеи

### Улучшить документацию
- Исправляйте опечатки и неточности
- Добавляйте примеры использования
- Переводите документацию на другие языки
- Улучшайте существующие руководства

### Написать код
- Выберите задачу из Issues с меткой `good first issue` или `help wanted`
- Исправляйте баги
- Реализуйте новые функции
- Оптимизируйте производительность
- Добавляйте тесты

## 🚀 С чего начать

### Настройка окружения разработки

1. **Форкните репозиторий**
   ```bash
   # Нажмите кнопку Fork на GitHub
   ```

2. **Клонируйте свой форк**
   ```bash
   git clone https://github.com/YOUR-USERNAME/hybrid-rag-system.git
   cd hybrid-rag-system
   ```

3. **Добавьте upstream репозиторий**
   ```bash
   git remote add upstream https://github.com/Rivega42/hybrid-rag-system.git
   ```

4. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate  # Windows
   ```

5. **Установите зависимости**
   ```bash
   pip install -e ".[dev]"
   pre-commit install
   ```

6. **Запустите тесты**
   ```bash
   pytest
   ```

## 💻 Процесс разработки

### 1. Создайте новую ветку
```bash
# Обновите main ветку
git checkout main
git pull upstream main

# Создайте feature ветку
git checkout -b feature/your-feature-name
# или для исправления бага
git checkout -b fix/bug-description
```

### 2. Внесите изменения
- Пишите понятный и поддерживаемый код
- Следуйте существующей архитектуре
- Добавляйте комментарии на русском языке
- Обновляйте документацию при необходимости

### 3. Добавьте тесты
```python
# tests/test_your_feature.py
def test_new_feature():
    """Тест новой функциональности."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    assert result == expected
```

### 4. Проверьте код
```bash
# Запустите линтеры
black .
isort .
flake8
mypy .

# Запустите тесты
pytest --cov=hybrid_rag
```

### 5. Закоммитьте изменения
```bash
git add .
git commit -m "feat: Добавлена поддержка нового типа агентов"
```

### Формат commit-сообщений

Используйте следующий формат:
- `feat:` - новая функция
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `style:` - форматирование кода
- `refactor:` - рефакторинг кода
- `test:` - добавление тестов
- `chore:` - обновление сборки, зависимостей и т.д.

## 🎨 Стиль кода

### Python
- Следуйте PEP 8
- Используйте type hints
- Максимальная длина строки - 100 символов
- Используйте Black для форматирования
- Сортируйте импорты с isort

```python
# Хороший пример
from typing import List, Optional

def process_query(
    query: str,
    max_results: int = 10,
    filters: Optional[List[str]] = None
) -> QueryResult:
    """Обработка поискового запроса.
    
    Args:
        query: Текст запроса
        max_results: Максимальное количество результатов
        filters: Дополнительные фильтры
    
    Returns:
        QueryResult: Результат обработки запроса
    """
    # Реализация
    ...
```

### Документация
- Все публичные функции и классы должны иметь docstrings
- Используйте Google-style docstrings
- Комментарии в коде - на русском языке
- README и документация - на русском языке

## 🧪 Тестирование

### Структура тестов
```
tests/
├── unit/           # Юнит-тесты
├── integration/    # Интеграционные тесты
├── e2e/           # End-to-end тесты
└── fixtures/      # Тестовые данные
```

### Запуск тестов
```bash
# Все тесты
pytest

# Только юнит-тесты
pytest tests/unit

# С покрытием
pytest --cov=hybrid_rag --cov-report=html

# Конкретный тест
pytest tests/unit/test_router.py::test_routing_decision
```

### Написание тестов
```python
import pytest
from hybrid_rag import HybridRAG

@pytest.fixture
def rag_instance():
    """Фикстура для создания экземпляра RAG."""
    return HybridRAG(cache_enabled=False)

def test_simple_query(rag_instance):
    """Тест обработки простого запроса."""
    result = rag_instance.query("Тестовый запрос")
    
    assert result is not None
    assert result.strategy_used == RoutingStrategy.CLASSIC_RAG
    assert result.latency_ms < 1000
```

## 🚢 Создание Pull Request

### 1. Отправьте изменения в свой форк
```bash
git push origin feature/your-feature-name
```

### 2. Создайте Pull Request
- Перейдите на GitHub
- Нажмите "New Pull Request"
- Выберите вашу ветку
- Заполните шаблон PR

### Шаблон Pull Request
```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Исправление бага (non-breaking change)
- [ ] Новая функция (non-breaking change)
- [ ] Breaking change
- [ ] Требует обновления документации

## Как протестировано?
Опишите тесты, которые вы провели

## Чеклист
- [ ] Код следует стилю проекта
- [ ] Добавлены тесты
- [ ] Все тесты проходят
- [ ] Обновлена документация
- [ ] Добавлены комментарии на русском языке
```

### 3. Процесс ревью
- Maintainer'ы проведут code review
- Отвечайте на комментарии и вопросы
- Вносите запрошенные изменения
- После одобрения PR будет смержен

## 🐛 Сообщение о проблемах

### Создание Issue

Используйте соответствующий шаблон:
- **Bug Report** - для сообщения об ошибках
- **Feature Request** - для предложения новых функций
- **Documentation** - для проблем с документацией

### Информация для Bug Report

1. **Описание проблемы**
2. **Шаги для воспроизведения**
3. **Ожидаемое поведение**
4. **Фактическое поведение**
5. **Скриншоты** (если применимо)
6. **Окружение:**
   - ОС: [например, Ubuntu 22.04]
   - Python версия: [например, 3.11.5]
   - Версия проекта: [например, 0.1.0]

## 📚 Полезные ресурсы

- [Документация проекта](https://hrag.mixbase.ru/docs)
- [API Reference](https://hrag.mixbase.ru/api)
- [Архитектура системы](ARCHITECTURE.md)
- [Roadmap](https://hrag.mixbase.ru/roadmap)
- [Telegram сообщество](https://t.me/hybrid_rag_ru)

## ❓ Вопросы?

Если у вас есть вопросы:
1. Проверьте [FAQ](https://hrag.mixbase.ru/faq)
2. Поищите в [Issues](https://github.com/Rivega42/hybrid-rag-system/issues)
3. Спросите в [Telegram](https://t.me/hybrid_rag_ru)
4. Создайте новый Issue с меткой `question`

## 🙏 Благодарности

Спасибо всем, кто вносит вклад в развитие проекта! Каждый PR, Issue, и даже звёздочка на GitHub важны для нас.

---

**Примечание:** Это руководство является живым документом и может обновляться. Следите за изменениями!