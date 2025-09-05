# Multi-stage Dockerfile для Hybrid RAG System
# Stage 1: Builder
FROM python:3.11-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для запуска приложения
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv

# Настройка переменных окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Создание рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY --chown=appuser:appuser . /app

# Создание директорий для данных
RUN mkdir -p /app/data /app/logs /app/models && \
    chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Экспозиция порта
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]