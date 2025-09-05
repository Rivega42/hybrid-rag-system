# Dockerfile для Hybrid RAG System
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .
COPY setup.py .
COPY pyproject.toml .
COPY README.md .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/

# Создание необходимых директорий
RUN mkdir -p /app/data /app/logs /app/models

# Установка пакета
RUN pip install -e .

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Запуск API сервера
CMD ["uvicorn", "src.hybrid_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]