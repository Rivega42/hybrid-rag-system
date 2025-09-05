# Multi-stage build для оптимизации размера образа
# Стадия 1: Сборка зависимостей
FROM python:3.11-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов с требованиями
COPY requirements.txt /tmp/

# Установка Python зависимостей
RUN pip install --user --no-cache-dir -r /tmp/requirements.txt

# Стадия 2: Финальный образ
FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="Hybrid RAG Team <support@mixbase.ru>"
LABEL description="Production-ready гибридная RAG система"
LABEL version="0.1.0"

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Установка системных зависимостей для runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r hybridrag && useradd -r -g hybridrag hybridrag

# Создание рабочей директории
WORKDIR /app

# Копирование зависимостей из builder
COPY --from=builder /root/.local /home/hybridrag/.local

# Копирование исходного кода
COPY src/ /app/src/
COPY setup.py /app/
COPY pyproject.toml /app/
COPY README.md /app/

# Установка пакета
RUN pip install --no-cache-dir -e .

# Изменение владельца файлов
RUN chown -R hybridrag:hybridrag /app

# Переключение на пользователя
USER hybridrag

# Добавление локальных бинарников в PATH
ENV PATH=/home/hybridrag/.local/bin:$PATH

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "src.hybrid_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]