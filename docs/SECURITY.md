# 🔒 Руководство по безопасности

## 📋 Содержание

- [Политика безопасности](#политика-безопасности)
- [Аутентификация и авторизация](#аутентификация-и-авторизация)
- [Шифрование данных](#шифрование-данных)
- [Защита API](#защита-api)
- [Безопасность инфраструктуры](#безопасность-инфраструктуры)
- [Аудит и мониторинг](#аудит-и-мониторинг)
- [Управление секретами](#управление-секретами)
- [Защита от атак](#защита-от-атак)
- [Compliance и соответствие](#compliance-и-соответствие)
- [Incident Response](#incident-response)
- [Чеклист безопасности](#чеклист-безопасности)

## Политика безопасности

### Принципы безопасности

1. **Defense in Depth** - Многоуровневая защита
2. **Least Privilege** - Минимальные привилегии
3. **Zero Trust** - Нулевое доверие
4. **Security by Design** - Безопасность на этапе проектирования
5. **Continuous Security** - Непрерывная безопасность

### Ответственное раскрытие уязвимостей

Если вы обнаружили уязвимость:

1. **НЕ** публикуйте информацию публично
2. Отправьте детали на security@mixbase.ru
3. Используйте PGP ключ для шифрования (ID: 0x1234ABCD)
4. Ожидайте ответа в течение 48 часов
5. Получите благодарность и возможное вознаграждение

## Аутентификация и авторизация

### JWT аутентификация

```python
# security/jwt_auth.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class JWTManager:
    """Менеджер JWT токенов"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=1)
        self.refresh_expiry = timedelta(days=7)
        
    def generate_token(self, user_id: str, claims: Dict[str, Any] = None) -> str:
        """Генерация access токена"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if claims:
            payload.update(claims)
            
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
    def generate_refresh_token(self, user_id: str) -> str:
        """Генерация refresh токена"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + self.refresh_expiry,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Верификация токена"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Токен истек")
        except jwt.InvalidTokenError:
            raise Exception("Невалидный токен")
```

### OAuth 2.0 интеграция

```python
# security/oauth.py
from authlib.integrations.fastapi_client import OAuth
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI()
oauth = OAuth(app)

# Регистрация провайдеров
oauth.register(
    name='google',
    client_id='your-client-id',
    client_secret='your-client-secret',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get('/login/{provider}')
async def login(provider: str, request: Request):
    """Инициация OAuth flow"""
    redirect_uri = request.url_for('callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(
        request, redirect_uri
    )

@app.get('/callback/{provider}')
async def callback(provider: str, request: Request):
    """OAuth callback"""
    token = await oauth.create_client(provider).authorize_access_token(request)
    user_info = token.get('userinfo')
    
    # Создание JWT токена для пользователя
    jwt_token = jwt_manager.generate_token(
        user_id=user_info['sub'],
        claims={'email': user_info['email']}
    )
    
    return {"access_token": jwt_token}
```

### Role-Based Access Control (RBAC)

```python
# security/rbac.py
from enum import Enum
from typing import List, Set
from functools import wraps

class Role(Enum):
    """Роли пользователей"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_CLIENT = "api_client"

class Permission(Enum):
    """Разрешения"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE_AGENTIC = "execute_agentic"
    VIEW_ANALYTICS = "view_analytics"

# Матрица разрешений
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.ADMIN,
        Permission.EXECUTE_AGENTIC,
        Permission.VIEW_ANALYTICS
    },
    Role.USER: {
        Permission.READ,
        Permission.WRITE,
        Permission.EXECUTE_AGENTIC
    },
    Role.VIEWER: {
        Permission.READ,
        Permission.VIEW_ANALYTICS
    },
    Role.API_CLIENT: {
        Permission.READ,
        Permission.EXECUTE_AGENTIC
    }
}

def require_permission(permission: Permission):
    """Декоратор для проверки разрешений"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.user
            user_role = Role(user.role)
            
            if permission not in ROLE_PERMISSIONS.get(user_role, set()):
                raise PermissionError(f"Недостаточно прав для {permission.value}")
                
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Использование
@require_permission(Permission.EXECUTE_AGENTIC)
async def execute_agentic_rag(request, query: str):
    """Только для пользователей с правом EXECUTE_AGENTIC"""
    return await agentic_rag.process(query)
```

## Шифрование данных

### Шифрование в покое (At Rest)

```python
# security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class EncryptionManager:
    """Менеджер шифрования данных"""
    
    def __init__(self, master_key: str = None):
        if master_key:
            self.cipher = Fernet(master_key)
        else:
            self.cipher = Fernet(Fernet.generate_key())
            
    @classmethod
    def derive_key(cls, password: str, salt: bytes = None) -> bytes:
        """Деривация ключа из пароля"""
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
        
    def encrypt(self, data: str) -> str:
        """Шифрование данных"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрование данных"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
        
    def encrypt_field(self, value: Any, field_type: str = "string") -> str:
        """Шифрование поля БД"""
        if field_type == "json":
            value = json.dumps(value)
        return self.encrypt(str(value))
        
    def decrypt_field(self, encrypted_value: str, field_type: str = "string") -> Any:
        """Дешифрование поля БД"""
        decrypted = self.decrypt(encrypted_value)
        
        if field_type == "json":
            return json.loads(decrypted)
        elif field_type == "int":
            return int(decrypted)
        elif field_type == "float":
            return float(decrypted)
        return decrypted
```

### Шифрование в передаче (In Transit)

```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name api.hybrid-rag.ru;
    
    # SSL сертификаты
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # Современные настройки SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/nginx/ssl/chain.pem;
    
    location / {
        proxy_pass http://hybrid-rag:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Защита API

### Rate Limiting

```python
# security/rate_limiting.py
from typing import Optional
import time
import redis
from functools import wraps

class RateLimiter:
    """Rate limiter на основе Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    def is_allowed(
        self, 
        key: str, 
        max_requests: int, 
        window: int
    ) -> tuple[bool, Optional[int]]:
        """Проверка лимита запросов"""
        current = int(time.time())
        window_start = current - window
        
        # Удаляем старые записи
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Подсчитываем запросы в окне
        request_count = self.redis.zcard(key)
        
        if request_count < max_requests:
            # Добавляем текущий запрос
            self.redis.zadd(key, {str(current): current})
            self.redis.expire(key, window)
            return True, None
        else:
            # Вычисляем время до сброса
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1]) + window - current
                return False, reset_time
            return False, window

def rate_limit(max_requests: int = 60, window: int = 60):
    """Декоратор для rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Получаем идентификатор клиента
            client_id = request.headers.get("X-API-Key") or request.client.host
            key = f"rate_limit:{client_id}:{func.__name__}"
            
            allowed, retry_after = rate_limiter.is_allowed(
                key, max_requests, window
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)}
                )
                
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### API Key Management

```python
# security/api_keys.py
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List

class APIKeyManager:
    """Менеджер API ключей"""
    
    def __init__(self, db_session):
        self.db = db_session
        
    def generate_api_key(
        self, 
        user_id: str, 
        name: str,
        permissions: List[str],
        expires_in: Optional[timedelta] = None
    ) -> str:
        """Генерация нового API ключа"""
        # Генерируем случайный ключ
        raw_key = secrets.token_urlsafe(32)
        
        # Хешируем для хранения
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Сохраняем в БД
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=datetime.utcnow() + expires_in if expires_in else None,
            created_at=datetime.utcnow(),
            last_used=None
        )
        self.db.add(api_key)
        self.db.commit()
        
        # Возвращаем сырой ключ (показывается только один раз)
        return raw_key
        
    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Валидация API ключа"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash
        ).first()
        
        if not api_key:
            return None
            
        # Проверяем срок действия
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
            
        # Обновляем время последнего использования
        api_key.last_used = datetime.utcnow()
        self.db.commit()
        
        return api_key
        
    def revoke_api_key(self, key_id: str) -> bool:
        """Отзыв API ключа"""
        api_key = self.db.query(APIKey).filter(
            APIKey.id == key_id
        ).first()
        
        if api_key:
            api_key.revoked = True
            api_key.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
```

### Input Validation

```python
# security/validation.py
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import re
import bleach

class QueryInput(BaseModel):
    """Валидация входящих запросов"""
    
    query: str = Field(..., min_length=1, max_length=10000)
    language: str = Field("ru", regex="^[a-z]{2}$")
    max_tokens: int = Field(2000, ge=1, le=10000)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    
    @validator('query')
    def sanitize_query(cls, v):
        """Санитизация запроса"""
        # Удаляем потенциально опасные HTML теги
        v = bleach.clean(v, tags=[], strip=True)
        
        # Проверяем на SQL injection паттерны
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(--|#|/\*|\*/)",
            r"(\bUNION\b.*\bSELECT\b)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Обнаружен подозрительный паттерн")
                
        return v
        
    @validator('max_tokens')
    def validate_tokens_limit(cls, v, values):
        """Проверка лимита токенов в зависимости от роли"""
        # Здесь можно добавить логику проверки прав пользователя
        user_role = values.get('user_role', 'user')
        
        if user_role == 'user' and v > 5000:
            raise ValueError("Превышен лимит токенов для вашей роли")
            
        return v
```

## Безопасность инфраструктуры

### Docker Security

```dockerfile
# Dockerfile с best practices безопасности
FROM python:3.11-slim AS builder

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 appuser && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production образ
FROM python:3.11-slim

# Копируем пользователя из builder
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Копируем зависимости
COPY --from=builder --chown=appuser:appuser /home/appuser/.local /home/appuser/.local

WORKDIR /app

# Копируем приложение
COPY --chown=appuser:appuser . .

# Переключаемся на непривилегированного пользователя
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Запуск от непривилегированного пользователя
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Security

```yaml
# k8s/security-policies.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hybrid-rag-sa
  namespace: hybrid-rag
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: hybrid-rag
  name: hybrid-rag-role
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: hybrid-rag-rolebinding
  namespace: hybrid-rag
subjects:
  - kind: ServiceAccount
    name: hybrid-rag-sa
    namespace: hybrid-rag
roleRef:
  kind: Role
  name: hybrid-rag-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: policy/v1
kind: PodSecurityPolicy
metadata:
  name: hybrid-rag-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

### Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: hybrid-rag-netpol
  namespace: hybrid-rag
spec:
  podSelector:
    matchLabels:
      app: hybrid-rag
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: databases
      ports:
        - protocol: TCP
          port: 5432  # PostgreSQL
        - protocol: TCP
          port: 6379  # Redis
    - to:
        - podSelector:
            matchLabels:
              app: qdrant
      ports:
        - protocol: TCP
          port: 6333
```

## Аудит и мониторинг

### Audit Logging

```python
# security/audit.py
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class AuditEventType(Enum):
    """Типы событий аудита"""
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_ALERT = "security_alert"

class AuditLogger:
    """Система аудита"""
    
    def __init__(self, storage):
        self.storage = storage
        
    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Логирование события"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details
        }
        
        # Сохраняем в хранилище
        await self.storage.save_audit_event(event)
        
        # Проверяем на критические события
        if event_type == AuditEventType.SECURITY_ALERT:
            await self._handle_security_alert(event)
            
    async def _handle_security_alert(self, event: Dict[str, Any]):
        """Обработка security алертов"""
        # Отправка уведомлений
        await notification_service.send_alert(
            title="Security Alert",
            message=json.dumps(event),
            severity="high"
        )
        
        # Возможная блокировка пользователя
        if event['details'].get('auto_block'):
            await user_service.block_user(event['user_id'])
```

### Security Monitoring

```python
# monitoring/security_metrics.py
from prometheus_client import Counter, Histogram

# Метрики безопасности
failed_auth_counter = Counter(
    'security_failed_auth_total',
    'Количество неудачных попыток аутентификации',
    ['method', 'reason']
)

suspicious_activity_counter = Counter(
    'security_suspicious_activity_total',
    'Количество подозрительных действий',
    ['type', 'severity']
)

api_key_usage = Counter(
    'security_api_key_usage_total',
    'Использование API ключей',
    ['key_id', 'endpoint']
)

encryption_operations = Histogram(
    'security_encryption_duration_seconds',
    'Время выполнения операций шифрования',
    ['operation']
)
```

## Управление секретами

### HashiCorp Vault Integration

```python
# security/vault.py
import hvac
from typing import Dict, Any, Optional

class VaultManager:
    """Менеджер для работы с HashiCorp Vault"""
    
    def __init__(self, vault_url: str, token: str):
        self.client = hvac.Client(url=vault_url, token=token)
        
        if not self.client.is_authenticated():
            raise Exception("Не удалось аутентифицироваться в Vault")
            
    def get_secret(self, path: str) -> Dict[str, Any]:
        """Получение секрета"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point="secret"
        )
        return response['data']['data']
        
    def store_secret(self, path: str, secret: Dict[str, Any]):
        """Сохранение секрета"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret,
            mount_point="secret"
        )
        
    def rotate_database_credentials(self, database: str) -> Dict[str, str]:
        """Ротация credentials базы данных"""
        response = self.client.secrets.database.generate_credentials(
            name=database
        )
        return {
            "username": response['data']['username'],
            "password": response['data']['password']
        }
```

### Environment Variables Security

```python
# security/env_manager.py
import os
from typing import Optional
from cryptography.fernet import Fernet

class SecureEnvironment:
    """Безопасное управление переменными окружения"""
    
    def __init__(self, key_file: str = ".env.key"):
        self.key = self._load_or_generate_key(key_file)
        self.cipher = Fernet(self.key)
        
    def _load_or_generate_key(self, key_file: str) -> bytes:
        """Загрузка или генерация ключа шифрования"""
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Только для владельца
            return key
            
    def get_secure_env(self, key: str, encrypted: bool = False) -> Optional[str]:
        """Получение переменной окружения"""
        value = os.getenv(key)
        
        if value and encrypted:
            # Дешифруем значение
            value = self.cipher.decrypt(value.encode()).decode()
            
        return value
        
    def set_secure_env(self, key: str, value: str, encrypt: bool = False):
        """Установка переменной окружения"""
        if encrypt:
            value = self.cipher.encrypt(value.encode()).decode()
            
        os.environ[key] = value
```

## Защита от атак

### SQL Injection Prevention

```python
# security/sql_protection.py
from sqlalchemy import text
from typing import Any, Dict

class SafeQueryBuilder:
    """Безопасный построитель SQL запросов"""
    
    @staticmethod
    def safe_query(query_template: str, params: Dict[str, Any]):
        """Безопасное выполнение SQL запроса"""
        # Используем параметризованные запросы
        stmt = text(query_template)
        
        # Валидация параметров
        for key, value in params.items():
            if isinstance(value, str):
                # Проверка на опасные паттерны
                if any(danger in value.upper() for danger in [
                    'DROP', 'DELETE', 'INSERT', 'UPDATE', '--', '/*'
                ]):
                    raise ValueError(f"Опасный паттерн в параметре {key}")
                    
        return stmt, params
```

### XSS Prevention

```python
# security/xss_protection.py
import bleach
from markupsafe import escape

class XSSProtection:
    """Защита от XSS атак"""
    
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    
    @classmethod
    def sanitize_html(cls, html: str) -> str:
        """Санитизация HTML"""
        return bleach.clean(
            html,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
    @classmethod
    def escape_output(cls, text: str) -> str:
        """Экранирование вывода"""
        return escape(text)
```

### CSRF Protection

```python
# security/csrf.py
import secrets
from fastapi import Request, HTTPException
from typing import Optional

class CSRFProtection:
    """Защита от CSRF атак"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        
    def generate_token(self) -> str:
        """Генерация CSRF токена"""
        return secrets.token_urlsafe(32)
        
    def validate_token(self, request: Request, token: Optional[str]) -> bool:
        """Валидация CSRF токена"""
        session_token = request.session.get('csrf_token')
        
        if not session_token or not token:
            return False
            
        return secrets.compare_digest(session_token, token)
        
    async def csrf_protect(self, request: Request):
        """Middleware для CSRF защиты"""
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token')
            
            if not self.validate_token(request, token):
                raise HTTPException(
                    status_code=403,
                    detail="CSRF token validation failed"
                )
```

## Compliance и соответствие

### GDPR Compliance

```python
# compliance/gdpr.py
from typing import Dict, Any, List
from datetime import datetime

class GDPRCompliance:
    """Обеспечение соответствия GDPR"""
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Экспорт данных пользователя (Right to Access)"""
        data = {
            "user_info": await self._get_user_info(user_id),
            "queries": await self._get_user_queries(user_id),
            "documents": await self._get_user_documents(user_id),
            "audit_log": await self._get_user_audit_log(user_id)
        }
        
        return data
        
    async def delete_user_data(self, user_id: str) -> bool:
        """Удаление данных пользователя (Right to be Forgotten)"""
        # Анонимизация вместо полного удаления для аудита
        await self._anonymize_user_data(user_id)
        
        # Удаление персональных данных
        await self._delete_personal_data(user_id)
        
        # Логирование удаления
        await audit_logger.log_event(
            AuditEventType.DATA_MODIFICATION,
            user_id=user_id,
            details={"action": "gdpr_deletion"}
        )
        
        return True
        
    async def get_consent_status(self, user_id: str) -> Dict[str, bool]:
        """Получение статуса согласий пользователя"""
        return {
            "data_processing": await self._check_consent(user_id, "data_processing"),
            "marketing": await self._check_consent(user_id, "marketing"),
            "analytics": await self._check_consent(user_id, "analytics"),
            "third_party": await self._check_consent(user_id, "third_party")
        }
```

### SOC2 Compliance

```python
# compliance/soc2.py
class SOC2Compliance:
    """Обеспечение соответствия SOC2"""
    
    def __init__(self):
        self.controls = {
            "CC1.1": "Logical Access Controls",
            "CC1.2": "User Access Provisioning",
            "CC1.3": "User Authentication",
            "CC2.1": "Baseline Configuration",
            "CC2.2": "Change Management",
            "CC2.3": "System Monitoring",
            "CC3.1": "Data at Rest Encryption",
            "CC3.2": "Data in Transit Encryption",
            "CC4.1": "Environmental Protection",
            "CC4.2": "Physical Access Controls"
        }
        
    async def audit_control(self, control_id: str) -> Dict[str, Any]:
        """Аудит конкретного контроля"""
        if control_id not in self.controls:
            raise ValueError(f"Unknown control: {control_id}")
            
        # Выполнение проверок для контроля
        result = await self._check_control(control_id)
        
        return {
            "control_id": control_id,
            "description": self.controls[control_id],
            "status": result["status"],
            "evidence": result["evidence"],
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Incident Response

### План реагирования на инциденты

```python
# security/incident_response.py
from enum import Enum
from typing import List, Dict, Any

class IncidentSeverity(Enum):
    """Уровни серьезности инцидентов"""
    CRITICAL = "critical"  # Утечка данных, взлом
    HIGH = "high"         # Попытка взлома, DoS
    MEDIUM = "medium"     # Подозрительная активность
    LOW = "low"           # Минимальное воздействие

class IncidentResponse:
    """Система реагирования на инциденты"""
    
    def __init__(self):
        self.response_team = {
            IncidentSeverity.CRITICAL: ["cto@mixbase.ru", "security@mixbase.ru"],
            IncidentSeverity.HIGH: ["security@mixbase.ru", "devops@mixbase.ru"],
            IncidentSeverity.MEDIUM: ["devops@mixbase.ru"],
            IncidentSeverity.LOW: ["monitoring@mixbase.ru"]
        }
        
    async def report_incident(
        self,
        severity: IncidentSeverity,
        description: str,
        affected_systems: List[str],
        evidence: Dict[str, Any]
    ):
        """Репортинг инцидента"""
        incident = {
            "id": self._generate_incident_id(),
            "severity": severity.value,
            "description": description,
            "affected_systems": affected_systems,
            "evidence": evidence,
            "reported_at": datetime.utcnow().isoformat(),
            "status": "open"
        }
        
        # Сохранение инцидента
        await self._save_incident(incident)
        
        # Уведомление команды
        await self._notify_response_team(incident)
        
        # Автоматические действия
        if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            await self._initiate_automatic_response(incident)
            
        return incident["id"]
        
    async def _initiate_automatic_response(self, incident: Dict[str, Any]):
        """Автоматическое реагирование"""
        # Блокировка подозрительных IP
        if "ip_addresses" in incident["evidence"]:
            for ip in incident["evidence"]["ip_addresses"]:
                await firewall.block_ip(ip)
                
        # Отзыв скомпрометированных ключей
        if "api_keys" in incident["evidence"]:
            for key in incident["evidence"]["api_keys"]:
                await api_key_manager.revoke_api_key(key)
                
        # Включение повышенного логирования
        await logging_service.set_level("DEBUG")
```

## Чеклист безопасности

### Pre-Production чеклист

```yaml
# security-checklist.yaml
authentication:
  - [ ] JWT токены настроены с безопасным секретом
  - [ ] Refresh токены реализованы
  - [ ] OAuth 2.0 провайдеры настроены
  - [ ] MFA включена для админов

authorization:
  - [ ] RBAC настроен
  - [ ] Проверка прав на все endpoints
  - [ ] Принцип наименьших привилегий

encryption:
  - [ ] TLS 1.2+ для всех соединений
  - [ ] Шифрование в покое для БД
  - [ ] Ключи шифрования в безопасном хранилище

api_security:
  - [ ] Rate limiting включен
  - [ ] Input validation на всех endpoints
  - [ ] CORS правильно настроен
  - [ ] API ключи хешированы

infrastructure:
  - [ ] Контейнеры запускаются от non-root
  - [ ] Network policies настроены
  - [ ] Security groups минимальны
  - [ ] Secrets в Kubernetes зашифрованы

monitoring:
  - [ ] Аудит логирование включено
  - [ ] Security метрики настроены
  - [ ] Алерты настроены
  - [ ] SIEM интеграция

compliance:
  - [ ] GDPR процессы внедрены
  - [ ] Data retention политика
  - [ ] Backup стратегия
  - [ ] Disaster recovery план

vulnerabilities:
  - [ ] Dependency scanning в CI/CD
  - [ ] Container scanning
  - [ ] SAST/DAST тестирование
  - [ ] Penetration testing проведен
```

### Production чеклист

```bash
#!/bin/bash
# security-check.sh - Скрипт проверки безопасности

echo "🔒 Проверка безопасности Hybrid RAG System..."

# Проверка SSL сертификатов
echo "Checking SSL certificates..."
openssl s_client -connect api.hybrid-rag.ru:443 -servername api.hybrid-rag.ru < /dev/null

# Проверка открытых портов
echo "Checking open ports..."
nmap -sT api.hybrid-rag.ru

# Проверка headers безопасности
echo "Checking security headers..."
curl -I https://api.hybrid-rag.ru | grep -E "(Strict-Transport|X-Frame|X-Content|CSP)"

# Проверка уязвимостей в зависимостях
echo "Scanning dependencies..."
safety check
pip-audit

# Проверка Docker образов
echo "Scanning Docker images..."
trivy image hybrid-rag:latest

echo "✅ Security check completed!"
```

---

**Важно**: Регулярно обновляйте все компоненты системы, проводите security аудиты и следите за CVE уязвимостями в используемых библиотеках. Безопасность - это непрерывный процесс, а не одноразовая настройка.
