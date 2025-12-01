# 🚀 Production Deployment Guide

Complete guide for deploying the RAG Pipeline to production with security, scalability, and monitoring.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Production-Grade Redis](#production-grade-redis)
3. [Worker Scaling](#worker-scaling)
4. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
5. [Authentication & Rate Limiting](#authentication--rate-limiting)
6. [Monitoring (Prometheus & Grafana)](#monitoring-prometheus--grafana)
7. [Logging (ELK Stack)](#logging-elk-stack)

---

## 1. Environment Variables

### Production `.env` Configuration

```bash
# Application
APP_ENV=production
API_TITLE="RAG Pipeline API"
API_VERSION="1.0.0"
DEBUG=false

# Redis Configuration
REDIS_URL=redis://redis-cluster:6379/0
REDIS_PASSWORD=your_secure_redis_password
REDIS_SSL=true
REDIS_MAX_CONNECTIONS=50

# OpenAI Configuration
OPENAI_API_KEY=sk-prod-your-key-here
OPENAI_ORG_ID=org-your-org-id

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
RETRIEVAL_TOP_K=5

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
API_KEY_HEADER=X-API-Key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Celery Configuration
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_RESULT_EXPIRES=3600

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
GRAFANA_PORT=3000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ELASTICSEARCH_HOST=elasticsearch:9200
ELASTICSEARCH_INDEX=rag-pipeline-logs
```

### Environment Variable Management

**Development:**
```bash
cp .env.example .env
# Edit .env with development values
```

**Production (Docker Secrets):**
```yaml
# docker-compose.prod.yml
services:
  api:
    environment:
      - REDIS_URL
      - OPENAI_API_KEY
    secrets:
      - redis_password
      - jwt_secret

secrets:
  redis_password:
    external: true
  jwt_secret:
    external: true
```

**Production (Kubernetes):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-pipeline-secrets
type: Opaque
data:
  redis-password: <base64-encoded>
  openai-api-key: <base64-encoded>
  jwt-secret: <base64-encoded>
```

---

## 2. Production-Grade Redis

### Option A: Redis Cluster (Self-Hosted)

**docker-compose.redis-cluster.yml:**
```yaml
version: '3.8'

services:
  redis-node-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "7001:6379"
    volumes:
      - redis-node-1-data:/data

  redis-node-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "7002:6379"
    volumes:
      - redis-node-2-data:/data

  redis-node-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --requirepass ${REDIS_PASSWORD}
    ports:
      - "7003:6379"
    volumes:
      - redis-node-3-data:/data

volumes:
  redis-node-1-data:
  redis-node-2-data:
  redis-node-3-data:
```

**Initialize Cluster:**
```bash
docker exec -it redis-node-1 redis-cli --cluster create \
  redis-node-1:6379 \
  redis-node-2:6379 \
  redis-node-3:6379 \
  --cluster-replicas 0 \
  -a ${REDIS_PASSWORD}
```

### Option B: Managed Redis Services

**AWS ElastiCache:**
```python
# src/core/config.py
REDIS_URL = "rediss://master.rag-cluster.abc123.use1.cache.amazonaws.com:6379/0"
REDIS_SSL = True
REDIS_SSL_CERT_REQS = "required"
```

**Azure Cache for Redis:**
```bash
REDIS_URL="rediss://rag-cache.redis.cache.windows.net:6380/0?ssl_cert_reqs=required"
```

**Google Cloud Memorystore:**
```bash
REDIS_URL="redis://10.0.0.3:6379/0"
```

### Redis Configuration for Production

**redis.conf:**
```conf
# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Security
requirepass your_secure_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""

# Performance
tcp-backlog 511
timeout 300
tcp-keepalive 300
```

---

## 3. Worker Scaling

### Horizontal Scaling (Docker Compose)

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  worker_default:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  worker_document:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G

  worker_vectorstore:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G

  worker_rag:
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

**Deploy:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

**k8s/worker-rag-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-worker-rag
spec:
  replicas: 5
  selector:
    matchLabels:
      app: rag-worker
      queue: rag
  template:
    metadata:
      labels:
        app: rag-worker
        queue: rag
    spec:
      containers:
      - name: worker
        image: rag-pipeline:latest
        command: ["celery", "-A", "src.workers.celery_worker.celery_app", "worker", "--loglevel=info", "--queues=rag", "--concurrency=4"]
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: openai-api-key
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-worker-rag-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-worker-rag
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Auto-Scaling Based on Queue Length

**celery-autoscaler.py:**
```python
import redis
import subprocess
import time

REDIS_URL = "redis://localhost:6379/0"
QUEUE_NAME = "rag"
MIN_WORKERS = 2
MAX_WORKERS = 10
SCALE_UP_THRESHOLD = 50
SCALE_DOWN_THRESHOLD = 10

def get_queue_length():
    r = redis.from_url(REDIS_URL)
    return r.llen(QUEUE_NAME)

def scale_workers(count):
    subprocess.run([
        "docker-compose", "up", "-d", "--scale", 
        f"worker_rag={count}"
    ])

current_workers = MIN_WORKERS

while True:
    queue_length = get_queue_length()
    
    if queue_length > SCALE_UP_THRESHOLD and current_workers < MAX_WORKERS:
        current_workers = min(current_workers + 2, MAX_WORKERS)
        scale_workers(current_workers)
        print(f"Scaled up to {current_workers} workers")
    
    elif queue_length < SCALE_DOWN_THRESHOLD and current_workers > MIN_WORKERS:
        current_workers = max(current_workers - 1, MIN_WORKERS)
        scale_workers(current_workers)
        print(f"Scaled down to {current_workers} workers")
    
    time.sleep(30)
```

---

## 4. Reverse Proxy (Nginx)

### Nginx Configuration

**nginx/nginx.conf:**
```nginx
upstream fastapi_backend {
    least_conn;
    server api:8000 max_fails=3 fail_timeout=30s;
    server api_2:8000 max_fails=3 fail_timeout=30s;
    server api_3:8000 max_fails=3 fail_timeout=30s;
}

upstream flower_backend {
    server flower:5555;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=query_limit:10m rate=20r/m;

server {
    listen 80;
    server_name api.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/api_access.log combined;
    error_log /var/log/nginx/api_error.log warn;

    # API Endpoints
    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        
        proxy_pass http://fastapi_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # RAG Query Endpoints (stricter rate limit)
    location /api/rag/query {
        limit_req zone=query_limit burst=5 nodelay;
        
        proxy_pass http://fastapi_backend/rag/query;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Health Check (no rate limit)
    location /health {
        proxy_pass http://fastapi_backend/health;
        access_log off;
    }

    # Flower Dashboard (protected)
    location /flower/ {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://flower_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Static files (if any)
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**docker-compose with Nginx:**
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/.htpasswd:/etc/nginx/.htpasswd:ro
    depends_on:
      - api
    restart: unless-stopped

  api:
    build: .
    expose:
      - "8000"
    deploy:
      replicas: 3
```

**Generate SSL Certificate (Let's Encrypt):**
```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Generate certificate
certbot --nginx -d api.example.com

# Auto-renewal
certbot renew --dry-run
```

**Create Basic Auth for Flower:**
```bash
htpasswd -c nginx/.htpasswd admin
```

---

## 5. Authentication & Rate Limiting

### API Key Authentication

**src/api/auth.py:**
```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from src.core.config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )
    
    # Check against database or environment variable
    valid_keys = settings.api_keys.split(",")
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    return api_key
```

**Apply to routes:**
```python
from fastapi import Depends
from src.api.auth import verify_api_key

@router.post("/rag/query", dependencies=[Depends(verify_api_key)])
async def query_vectorstore(request: QueryRequest):
    # Protected endpoint
    pass
```

### JWT Authentication

**src/api/jwt_auth.py:**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

**Login endpoint:**
```python
from src.api.jwt_auth import create_access_token

@router.post("/auth/login")
async def login(username: str, password: str):
    # Verify credentials (check database)
    if not verify_credentials(username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/rag/query", dependencies=[Depends(verify_token)])
async def query_vectorstore(request: QueryRequest):
    # Protected endpoint
    pass
```

### Rate Limiting with SlowAPI

**Install:**
```bash
pip install slowapi
```

**src/api/rate_limit.py:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# Add to main.py
from src.api.rate_limit import limiter, RateLimitExceeded, _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Apply rate limits:**
```python
from src.api.rate_limit import limiter

@router.post("/rag/query")
@limiter.limit("20/minute")
async def query_vectorstore(request: Request, query: QueryRequest):
    # Rate limited endpoint
    pass

@router.post("/tasks/calculate/add")
@limiter.limit("100/minute")
async def add_numbers(request: Request, data: AddNumbersRequest):
    # Different rate limit
    pass
```

### Redis-Based Rate Limiting

**src/api/redis_rate_limit.py:**
```python
import redis
from fastapi import HTTPException, Request
from datetime import datetime

redis_client = redis.from_url("redis://localhost:6379/0")

async def rate_limit(request: Request, max_requests: int = 60, window: int = 60):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}:{datetime.now().minute}"
    
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    
    if current > max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {max_requests} requests per {window} seconds"
        )
    
    return current

# Usage
@router.post("/rag/query")
async def query_vectorstore(request: Request, query: QueryRequest):
    await rate_limit(request, max_requests=20, window=60)
    # Process query
    pass
```

---

## 6. Monitoring (Prometheus & Grafana)

### Prometheus Setup

**prometheus/prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

**Add Prometheus to docker-compose:**
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis:6379
    restart: unless-stopped

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    ports:
      - "9113:9113"
    command:
      - '-nginx.scrape-uri=http://nginx:80/stub_status'
    restart: unless-stopped

volumes:
  prometheus-data:
```

### FastAPI Metrics

**Install:**
```bash
pip install prometheus-fastapi-instrumentator
```

**src/api/main.py:**
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
```

### Celery Metrics

**Install:**
```bash
pip install celery-exporter
```

**Start exporter:**
```bash
celery-exporter --broker-url=redis://localhost:6379/0
```

### Grafana Setup

**docker-compose:**
```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    restart: unless-stopped

volumes:
  grafana-data:
```

**grafana/datasources/prometheus.yml:**
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**grafana/dashboards/dashboard.json:**
```json
{
  "dashboard": {
    "title": "RAG Pipeline Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Task Queue Length",
        "targets": [
          {
            "expr": "celery_queue_length"
          }
        ]
      },
      {
        "title": "Worker Status",
        "targets": [
          {
            "expr": "celery_worker_up"
          }
        ]
      }
    ]
  }
}
```

**Access Grafana:**
```
URL: http://localhost:3000
Username: admin
Password: admin
```

### Key Metrics to Monitor

```promql
# API Request Rate
rate(http_requests_total[5m])

# API Response Time (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Rate
rate(http_requests_total{status=~"5.."}[5m])

# Celery Queue Length
celery_queue_length{queue="rag"}

# Celery Task Success Rate
rate(celery_task_succeeded_total[5m]) / rate(celery_task_total[5m])

# Redis Memory Usage
redis_memory_used_bytes / redis_memory_max_bytes

# Worker CPU Usage
rate(process_cpu_seconds_total[5m])
```

---

## 7. Logging (ELK Stack)

### ELK Stack Setup

**docker-compose.elk.yml:**
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    restart: unless-stopped

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    ports:
      - "5000:5000"
      - "9600:9600"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
    depends_on:
      - elasticsearch
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - elasticsearch
      - logstash
    restart: unless-stopped

volumes:
  elasticsearch-data:
```

### Logstash Configuration

**logstash/pipeline/logstash.conf:**
```conf
input {
  beats {
    port => 5000
  }
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [type] == "docker" {
    json {
      source => "message"
    }
    
    mutate {
      add_field => {
        "service" => "%{[docker][container][name]}"
      }
    }
  }
  
  # Parse FastAPI logs
  if [service] =~ "api" {
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{LOGLEVEL:level} - %{GREEDYDATA:log_message}"
      }
    }
  }
  
  # Parse Celery logs
  if [service] =~ "worker" {
    grok {
      match => {
        "message" => "\[%{TIMESTAMP_ISO8601:timestamp}\] \[%{WORD:level}\] %{GREEDYDATA:log_message}"
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "rag-pipeline-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => rubydebug
  }
}
```

### Filebeat Configuration

**filebeat/filebeat.yml:**
```yaml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

output.logstash:
  hosts: ["logstash:5000"]

logging.level: info
```

### Structured Logging in FastAPI

**src/core/logging_config.py:**
```python
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'rag-api'

def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

**src/api/main.py:**
```python
from src.core.logging_config import setup_logging

logger = setup_logging()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
            "client_ip": request.client.host
        }
    )
    
    return response
```

### Celery Logging

**src/tasks/basic_tasks.py:**
```python
import logging
from celery.signals import task_prerun, task_postrun, task_failure

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    logger.info(f"Task started: {task.name}", extra={
        "task_id": task_id,
        "task_name": task.name,
        "args": args,
        "kwargs": kwargs
    })

@task_postrun.connect
def task_postrun_handler(task_id, task, retval, *args, **kwargs):
    logger.info(f"Task completed: {task.name}", extra={
        "task_id": task_id,
        "task_name": task.name,
        "result": retval
    })

@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    logger.error(f"Task failed: {task_id}", extra={
        "task_id": task_id,
        "exception": str(exception)
    })
```

### Access Kibana

```
URL: http://localhost:5601
```

**Create Index Pattern:**
1. Go to Management → Stack Management → Index Patterns
2. Create pattern: `rag-pipeline-*`
3. Select timestamp field: `@timestamp`

**Useful Kibana Queries:**
```
# All errors
level: ERROR

# API requests
service: "rag_api" AND path: "/rag/query"

# Slow tasks
duration > 5000

# Failed tasks
status: "FAILURE"
```

---

## Complete Production docker-compose.yml

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

  # FastAPI Application
  api:
    build: .
    expose:
      - "8000"
    environment:
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    restart: unless-stopped

  # Celery Workers
  worker_rag:
    build: .
    command: celery -A src.workers.celery_worker.celery_app worker --loglevel=info --queues=rag --concurrency=4
    environment:
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '1'
          memory: 2G
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

  # Logging
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
  elasticsearch-data:
```

**Deploy:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
