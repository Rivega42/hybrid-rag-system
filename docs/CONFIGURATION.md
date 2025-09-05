# 🔧 Руководство по конфигурации

## 📋 Содержание

- [Переменные окружения](#переменные-окружения)
- [Конфигурационные файлы](#конфигурационные-файлы)
- [Настройка провайдеров](#настройка-провайдеров)
- [Конфигурация кэширования](#конфигурация-кэширования)
- [Настройка маршрутизации](#настройка-маршрутизации)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Профили конфигурации](#профили-конфигурации)
- [Валидация конфигурации](#валидация-конфигурации)

## Переменные окружения

### Основные переменные

```bash
# Режим работы системы
HRAG_ENV=production              # production | development | testing
HRAG_DEBUG=false                 # Включить отладочный режим
HRAG_LOG_LEVEL=INFO             # DEBUG | INFO | WARNING | ERROR | CRITICAL

# API сервер
HRAG_HOST=0.0.0.0               # IP адрес для привязки
HRAG_PORT=8000                  # Порт API сервера
HRAG_WORKERS=4                  # Количество воркеров
HRAG_MAX_REQUESTS=1000          # Максимум запросов на воркер

# Безопасность
HRAG_API_KEY=your-secret-key    # API ключ для доступа
HRAG_JWT_SECRET=jwt-secret      # Секрет для JWT токенов
HRAG_CORS_ORIGINS=*             # CORS разрешенные источники
```

### LLM провайдеры

```bash
# OpenAI
OPENAI_API_KEY=sk-...           # API ключ OpenAI
OPENAI_MODEL=gpt-4-turbo        # Модель по умолчанию
OPENAI_TEMPERATURE=0.7          # Температура генерации
OPENAI_MAX_TOKENS=2000          # Максимум токенов
OPENAI_TIMEOUT=30               # Таймаут запроса (сек)

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...    # API ключ Anthropic
ANTHROPIC_MODEL=claude-3-opus   # Модель Claude
ANTHROPIC_MAX_TOKENS=4000       # Максимум токенов

# Локальные модели (Ollama)
OLLAMA_HOST=http://localhost:11434  # Адрес Ollama сервера
OLLAMA_MODEL=llama2:70b            # Локальная модель
OLLAMA_TIMEOUT=60                   # Таймаут для больших моделей
```

### Векторные базы данных

```bash
# Qdrant
QDRANT_HOST=localhost           # Хост Qdrant
QDRANT_PORT=6333               # Порт Qdrant
QDRANT_API_KEY=                # API ключ (для cloud)
QDRANT_COLLECTION=documents    # Имя коллекции
QDRANT_VECTOR_SIZE=1536        # Размерность векторов

# Альтернативы
WEAVIATE_HOST=localhost:8080   # Weaviate endpoint
PINECONE_API_KEY=              # Pinecone API ключ
PINECONE_ENVIRONMENT=          # Pinecone окружение
```

### Кэширование

```bash
# Redis
REDIS_HOST=localhost            # Redis хост
REDIS_PORT=6379                # Redis порт
REDIS_PASSWORD=                # Redis пароль
REDIS_DB=0                     # Номер базы данных
REDIS_SSL=false                # Использовать SSL

# Настройки кэша
CACHE_L1_TTL=3600              # TTL для L1 кэша (сек)
CACHE_L2_TTL=7200              # TTL для L2 кэша (сек)
CACHE_L3_TTL=86400             # TTL для L3 кэша (сек)
CACHE_MAX_SIZE=10000           # Максимальный размер кэша
```

### Мониторинг

```bash
# Prometheus
PROMETHEUS_ENABLED=true        # Включить метрики
PROMETHEUS_PORT=9090          # Порт для метрик

# Grafana
GRAFANA_HOST=localhost         # Grafana хост
GRAFANA_PORT=3000             # Grafana порт

# Логирование
LOG_FILE_PATH=/var/log/hrag   # Путь к лог файлам
LOG_ROTATION=daily            # Ротация логов
LOG_BACKUP_COUNT=7            # Количество бэкапов
```

## Конфигурационные файлы

### config.yaml - Основной конфигурационный файл

```yaml
# config.yaml
version: "1.0"

# Общие настройки системы
system:
  name: "Hybrid RAG System"
  version: "0.1.0"
  language: "ru"  # Основной язык системы
  timezone: "Europe/Moscow"
  
# Настройки маршрутизации
routing:
  # Классификатор сложности запросов
  classifier:
    model: "distilbert-base-multilingual-cased"
    threshold_simple: 0.3      # Порог для простых запросов
    threshold_complex: 0.7     # Порог для сложных запросов
    cache_predictions: true    # Кэшировать предсказания
    
  # Стратегии обработки
  strategies:
    simple:
      handler: "classic_rag"
      max_chunks: 5            # Максимум чанков для поиска
      rerank: false           # Переранжирование
      
    medium:
      handler: "enhanced_rag"
      max_chunks: 10
      rerank: true
      rerank_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
      
    complex:
      handler: "agentic_rag"
      max_iterations: 5       # Максимум итераций агентов
      agents:
        - research
        - analysis
        - synthesis
      timeout: 30             # Таймаут в секундах

# Настройки Classic RAG
classic_rag:
  # Параметры поиска
  search:
    top_k: 10                 # Количество результатов
    score_threshold: 0.7      # Минимальный score
    hybrid_search: true       # Гибридный поиск (dense + sparse)
    
  # Обработка документов
  chunking:
    strategy: "recursive"     # recursive | fixed | semantic
    chunk_size: 512          # Размер чанка в токенах
    chunk_overlap: 50        # Перекрытие чанков
    
  # Embedding модель
  embeddings:
    model: "text-embedding-3-small"
    batch_size: 100
    normalize: true

# Настройки Agentic RAG
agentic_rag:
  # Оркестратор агентов
  orchestrator:
    strategy: "adaptive"      # adaptive | sequential | parallel
    max_parallel: 3          # Макс. параллельных агентов
    
  # Конфигурация агентов
  agents:
    research:
      model: "gpt-4-turbo"
      tools:
        - web_search
        - document_retrieval
        - sql_query
      max_iterations: 3
      
    analysis:
      model: "gpt-4-turbo"
      tools:
        - data_analysis
        - chart_generation
        - statistical_tests
      max_iterations: 2
      
    synthesis:
      model: "gpt-4-turbo"
      tools:
        - summarization
        - report_generation
      max_iterations: 1

# Настройки кэширования
cache:
  enabled: true
  
  # L1 - точные совпадения
  l1:
    type: "memory"           # memory | redis
    max_size: 1000
    ttl: 3600
    
  # L2 - семантическое сходство
  l2:
    type: "redis"
    similarity_threshold: 0.95
    max_size: 5000
    ttl: 7200
    
  # L3 - кэш путей поиска
  l3:
    type: "redis"
    max_paths: 100
    ttl: 86400

# Мониторинг и метрики
monitoring:
  # Prometheus метрики
  metrics:
    enabled: true
    port: 9090
    path: "/metrics"
    
  # Трейсинг
  tracing:
    enabled: true
    provider: "jaeger"       # jaeger | zipkin | datadog
    sampling_rate: 0.1      # 10% запросов
    
  # Алерты
  alerts:
    enabled: true
    channels:
      - email
      - slack
    rules:
      - metric: "latency_p95"
        threshold: 3000      # мс
        severity: "warning"
      - metric: "error_rate"
        threshold: 0.01      # 1%
        severity: "critical"

# Настройки безопасности
security:
  # Аутентификация
  auth:
    enabled: true
    type: "jwt"              # jwt | api_key | oauth2
    token_expiry: 3600       # секунды
    
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    requests_per_hour: 1000
    
  # Шифрование
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    
  # Аудит
  audit:
    enabled: true
    log_requests: true
    log_responses: false     # Для экономии места
    retention_days: 90

# Интеграции
integrations:
  # n8n
  n8n:
    enabled: true
    webhook_url: "${N8N_WEBHOOK_URL}"
    api_key: "${N8N_API_KEY}"
    timeout: 30
    
  # Slack
  slack:
    enabled: false
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#hybrid-rag"
    
  # Telegram
  telegram:
    enabled: false
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"

# Настройки для разных окружений
environments:
  # Продакшн
  production:
    debug: false
    log_level: "INFO"
    cache_enabled: true
    monitoring_enabled: true
    
  # Разработка
  development:
    debug: true
    log_level: "DEBUG"
    cache_enabled: false
    monitoring_enabled: false
    
  # Тестирование
  testing:
    debug: true
    log_level: "DEBUG"
    cache_enabled: false
    monitoring_enabled: false
    mock_llm: true           # Использовать mock LLM
```

### profiles/enterprise.yaml - Профиль для enterprise

```yaml
# profiles/enterprise.yaml
# Расширенная конфигурация для enterprise клиентов

extends: config.yaml

# Multi-tenancy
tenancy:
  enabled: true
  isolation_level: "strict"   # strict | shared | hybrid
  
  # Квоты на тенант
  quotas:
    max_requests_per_day: 10000
    max_storage_gb: 100
    max_concurrent_requests: 50
    
# SLA гарантии
sla:
  availability: 99.9          # Процент доступности
  latency_p95: 3000          # мс
  latency_p99: 5000          # мс
  
# Расширенная безопасность
security:
  compliance:
    - GDPR
    - SOC2
    - ISO27001
  
  data_residency:
    enabled: true
    regions:
      - eu-west-1
      - us-east-1
      
# Приоритетная поддержка
support:
  level: "platinum"
  response_time: "1h"
  dedicated_manager: true
```

## Настройка провайдеров

### OpenAI

```python
# providers/openai.py
from typing import Dict, Any

class OpenAIConfig:
    """Конфигурация для OpenAI провайдера"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-4-turbo')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.timeout = config.get('timeout', 30)
        
        # Расширенные настройки
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.organization_id = config.get('organization_id')
        
        # Настройки для разных моделей
        self.model_configs = {
            'gpt-4-turbo': {
                'max_tokens': 4000,
                'cost_per_1k_tokens': 0.01
            },
            'gpt-3.5-turbo': {
                'max_tokens': 2000,
                'cost_per_1k_tokens': 0.002
            }
        }
```

### Локальные модели (Ollama)

```python
# providers/ollama.py
class OllamaConfig:
    """Конфигурация для локальных моделей через Ollama"""
    
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('host', 'http://localhost:11434')
        self.model = config.get('model', 'llama2:70b')
        self.timeout = config.get('timeout', 60)
        
        # Оптимизация производительности
        self.num_ctx = config.get('num_ctx', 4096)  # Контекст
        self.num_gpu = config.get('num_gpu', 1)      # GPU слои
        self.num_thread = config.get('num_thread', 8) # CPU потоки
```

## Конфигурация кэширования

### Redis конфигурация

```python
# cache/redis_config.py
import redis
from typing import Optional

class RedisConfig:
    """Конфигурация Redis для кэширования"""
    
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.password = os.getenv('REDIS_PASSWORD')
        self.db = int(os.getenv('REDIS_DB', 0))
        self.ssl = os.getenv('REDIS_SSL', 'false').lower() == 'true'
        
        # Настройки пулов соединений
        self.max_connections = 50
        self.connection_timeout = 5
        
    def get_client(self) -> redis.Redis:
        """Получить клиент Redis с настройками"""
        pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            max_connections=self.max_connections,
            socket_connect_timeout=self.connection_timeout,
            decode_responses=True
        )
        return redis.Redis(connection_pool=pool)
```

### Стратегии инвалидации кэша

```python
# cache/invalidation.py
from enum import Enum
from typing import List, Optional

class InvalidationStrategy(Enum):
    """Стратегии инвалидации кэша"""
    TTL = "ttl"               # По времени жизни
    LRU = "lru"               # Least Recently Used
    LFU = "lfu"               # Least Frequently Used
    MANUAL = "manual"         # Ручная инвалидация
    EVENT_BASED = "event"     # По событиям

class CacheInvalidator:
    """Менеджер инвалидации кэша"""
    
    def __init__(self, strategy: InvalidationStrategy):
        self.strategy = strategy
        self.rules = []
        
    def add_rule(self, pattern: str, condition: str):
        """Добавить правило инвалидации"""
        self.rules.append({
            'pattern': pattern,
            'condition': condition
        })
        
    def should_invalidate(self, key: str) -> bool:
        """Проверить, нужна ли инвалидация"""
        for rule in self.rules:
            if self._match_pattern(key, rule['pattern']):
                if self._check_condition(key, rule['condition']):
                    return True
        return False
```

## Настройка маршрутизации

### Классификатор запросов

```python
# routing/classifier_config.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ClassifierConfig:
    """Конфигурация классификатора запросов"""
    
    # Модель классификации
    model_name: str = "distilbert-base-multilingual-cased"
    model_path: Optional[str] = None  # Путь к кастомной модели
    
    # Пороги классификации
    threshold_simple: float = 0.3
    threshold_medium: float = 0.6
    threshold_complex: float = 0.8
    
    # Правила классификации
    rules: List[Dict] = None
    
    # Признаки для классификации
    features: List[str] = [
        'query_length',        # Длина запроса
        'entity_count',        # Количество сущностей
        'question_type',       # Тип вопроса
        'temporal_markers',    # Временные маркеры
        'complexity_words',    # Слова-индикаторы сложности
    ]
    
    # Веса признаков
    feature_weights: Dict[str, float] = {
        'query_length': 0.1,
        'entity_count': 0.2,
        'question_type': 0.3,
        'temporal_markers': 0.2,
        'complexity_words': 0.2,
    }
```

### Правила маршрутизации

```yaml
# routing/rules.yaml
# Правила маршрутизации запросов

rules:
  # Простые запросы - Classic RAG
  - pattern: "^(что|кто|где|когда) (такое|такой|находится)"
    strategy: "classic_rag"
    confidence: 0.9
    
  - pattern: "определение|значение|перевод"
    strategy: "classic_rag"
    confidence: 0.85
    
  # Средние запросы - Enhanced RAG
  - pattern: "сравни|различия|преимущества"
    strategy: "enhanced_rag"
    confidence: 0.8
    
  - pattern: "найди.*(документ|файл|информацию)"
    strategy: "enhanced_rag"
    confidence: 0.75
    
  # Сложные запросы - Agentic RAG
  - pattern: "проанализируй|исследуй|изучи"
    strategy: "agentic_rag"
    confidence: 0.9
    
  - pattern: "влияние|взаимосвязь|корреляция"
    strategy: "agentic_rag"
    confidence: 0.85
    
  # Специальные случаи
  - pattern: "срочно|немедленно|быстро"
    strategy: "classic_rag"  # Для скорости
    confidence: 1.0
    override: true  # Переопределить ML классификацию
```

## Мониторинг и логирование

### Настройка Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'hybrid-rag'
    static_configs:
      - targets: ['localhost:9090']
    
    # Метрики для сбора
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'hrag_.*'
        action: keep
```

### Настройка логирования

```python
# logging_config.py
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filename': '/var/log/hrag/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': '/var/log/hrag/errors.log',
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    
    'loggers': {
        'hybrid_rag': {
            'level': 'DEBUG',
            'handlers': ['console', 'file', 'error_file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console']
        }
    },
    
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

## Профили конфигурации

### Использование профилей

```python
# config/profiles.py
from typing import Dict, Any
import yaml

class ConfigProfile:
    """Менеджер профилей конфигурации"""
    
    PROFILES = {
        'development': 'profiles/dev.yaml',
        'testing': 'profiles/test.yaml',
        'staging': 'profiles/staging.yaml',
        'production': 'profiles/prod.yaml',
        'enterprise': 'profiles/enterprise.yaml'
    }
    
    @classmethod
    def load_profile(cls, profile_name: str) -> Dict[str, Any]:
        """Загрузить профиль конфигурации"""
        if profile_name not in cls.PROFILES:
            raise ValueError(f"Неизвестный профиль: {profile_name}")
            
        profile_path = cls.PROFILES[profile_name]
        
        # Загружаем базовую конфигурацию
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            
        # Загружаем и мержим профиль
        with open(profile_path, 'r') as f:
            profile = yaml.safe_load(f)
            
        return cls._deep_merge(config, profile)
```

## Валидация конфигурации

### Схема валидации

```python
# config/validation.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict

class SystemConfig(BaseModel):
    """Схема валидации системной конфигурации"""
    
    name: str = Field(..., min_length=1)
    version: str = Field(..., regex=r'^\d+\.\d+\.\d+$')
    language: str = Field(default='ru', regex=r'^[a-z]{2}$')
    timezone: str
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Проверка валидности timezone"""
        import pytz
        if v not in pytz.all_timezones:
            raise ValueError(f'Неверный timezone: {v}')
        return v

class CacheConfig(BaseModel):
    """Схема валидации конфигурации кэширования"""
    
    enabled: bool = True
    l1_ttl: int = Field(3600, ge=0, le=86400)
    l2_ttl: int = Field(7200, ge=0, le=86400)
    l3_ttl: int = Field(86400, ge=0, le=604800)
    
    @validator('l2_ttl')
    def l2_greater_than_l1(cls, v, values):
        """L2 TTL должен быть больше L1"""
        if 'l1_ttl' in values and v <= values['l1_ttl']:
            raise ValueError('L2 TTL должен быть больше L1 TTL')
        return v

class ConfigValidator:
    """Валидатор конфигурации"""
    
    @staticmethod
    def validate(config: Dict[str, Any]) -> bool:
        """Валидировать полную конфигурацию"""
        try:
            # Валидация системных настроек
            SystemConfig(**config.get('system', {}))
            
            # Валидация кэширования
            CacheConfig(**config.get('cache', {}))
            
            # Дополнительные проверки
            ConfigValidator._validate_dependencies(config)
            ConfigValidator._validate_resources(config)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
```

## Примеры конфигурации для разных сценариев

### Минимальная конфигурация

```yaml
# config.minimal.yaml
# Минимальная конфигурация для быстрого старта

system:
  name: "Hybrid RAG"
  version: "0.1.0"

routing:
  classifier:
    model: "simple"  # Использовать простой классификатор

classic_rag:
  search:
    top_k: 5

cache:
  enabled: false  # Отключаем для простоты

monitoring:
  enabled: false
```

### High-Performance конфигурация

```yaml
# config.performance.yaml
# Оптимизация для максимальной производительности

system:
  workers: 16
  max_requests: 10000

routing:
  strategies:
    simple:
      handler: "classic_rag"
      cache_results: true
      parallel_search: true

cache:
  l1:
    type: "memory"
    max_size: 50000  # Большой кэш в памяти
    
  preload:
    enabled: true
    queries: "popular_queries.txt"

monitoring:
  metrics:
    sampling_rate: 0.01  # 1% для экономии ресурсов
```

### Secure конфигурация

```yaml
# config.secure.yaml
# Максимальная безопасность

security:
  auth:
    enabled: true
    type: "oauth2"
    providers:
      - google
      - github
    
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation: "weekly"
    
  audit:
    enabled: true
    log_everything: true
    retention_days: 365
    
  rate_limiting:
    enabled: true
    requests_per_minute: 10
    burst_size: 20
```

## Переменные окружения для Docker

```dockerfile
# .env.docker
# Переменные для Docker deployment

# Основные сервисы
COMPOSE_PROJECT_NAME=hybrid-rag
DOCKER_REGISTRY=registry.mixbase.ru

# Версии образов
HRAG_VERSION=0.1.0
REDIS_VERSION=7-alpine
POSTGRES_VERSION=15-alpine
QDRANT_VERSION=latest

# Сетевые настройки
HRAG_EXTERNAL_PORT=8000
REDIS_EXTERNAL_PORT=6379
QDRANT_EXTERNAL_PORT=6333

# Volumes
DATA_PATH=./data
LOGS_PATH=./logs
MODELS_PATH=./models
```

## Скрипты управления конфигурацией

### check-config.sh

```bash
#!/bin/bash
# Скрипт проверки конфигурации

echo "🔍 Проверка конфигурации Hybrid RAG System..."

# Проверка наличия файлов
files=("config.yaml" ".env")
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Файл $file не найден!"
        exit 1
    fi
done

# Валидация YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))" || {
    echo "❌ Ошибка в config.yaml"
    exit 1
}

# Проверка переменных окружения
required_vars=("OPENAI_API_KEY" "REDIS_HOST" "QDRANT_HOST")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "⚠️  Переменная $var не установлена"
    fi
done

echo "✅ Конфигурация валидна!"
```

---

**Примечание**: Все пути к файлам и переменные окружения должны быть адаптированы под вашу инфраструктуру. Рекомендуется использовать инструменты управления секретами (HashiCorp Vault, AWS Secrets Manager) для хранения чувствительных данных в production окружении.
