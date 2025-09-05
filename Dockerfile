# Многоступенчатая сборка для оптимизации размера образа
# Этап 1: Сборка зависимостей
FROM python:3.11-slim as builder

WORKDIR /app

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов с зависимостями
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --user -r requirements.txt

# Этап 2: Финальный образ
FROM python:3.11-slim

# Установка системных зависимостей для runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r hybridrag && useradd -r -g hybridrag hybridrag

WORKDIR /app

# Копирование установленных зависимостей из builder
COPY --from=builder /root/.local /root/.local

# Копирование кода приложения
COPY . .

# Установка переменных окружения
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Создание директорий для данных и логов
RUN mkdir -p /app/data /app/logs && \
    chown -R hybridrag:hybridrag /app

# Переключение на непривилегированного пользователя
USER hybridrag

# Открытие порта
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["python", "-m", "uvicorn", "src.hybrid_rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]