# 🔄 Queue Architecture

## Why Multi-Queue Architecture?

Traditional single-queue systems can become bottlenecks when handling diverse workloads. Our multi-queue architecture solves this by:

- **Isolating workloads** - CPU-intensive tasks don't block I/O operations
- **Optimizing resources** - Allocate workers based on task requirements
- **Improving reliability** - Failures in one queue don't cascade to others
- **Enabling scalability** - Scale specific queues independently based on demand
- **Reducing costs** - Run expensive operations (OpenAI API) only where needed

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI                             │
│                      (Task Router)                          │
└────┬────────────┬────────────┬────────────┬────────────────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ default │  │document │  │vectorstore│  │   rag   │
│  queue  │  │  queue  │  │   queue   │  │  queue  │
└────┬────┘  └────┬────┘  └────┬──────┘  └────┬────┘
     │            │            │              │
     ▼            ▼            ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ worker  │  │ worker  │  │ worker  │  │ worker  │
│ default │  │document │  │vectorstore│  │   rag   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
     │            │            │              │
     └────────────┴────────────┴──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │    Redis     │
              │ (Broker/Cache)│
              └──────────────┘
```

## Queue Specifications

### 🔧 Default Queue
**Queue Name:** `default`  
**Worker:** `worker_default`  
**Concurrency:** 2 workers  
**Dependencies:** None  
**Use Case:** General-purpose operations, demos, and lightweight tasks

| Task Name | Description | Retry Logic |
|-----------|-------------|-------------|
| `tasks.process_data` | Background data processing with 20s delay | No |
| `tasks.add_numbers` | Simple addition operation (demo) | No |
| `tasks.divide_numbers` | Division with zero-check (demo) | Yes (5 retries, exponential backoff) |
| `tasks.aggregate_results` | Sum results from parallel tasks | No |

**When to use:** Quick calculations, data transformations, non-blocking operations

---

### 📄 Document Queue
**Queue Name:** `document`  
**Worker:** `worker_document`  
**Concurrency:** 2 workers  
**Dependencies:** PyPDF2, LangChain  
**Use Case:** CPU-intensive document processing

| Task Name | Description | Average Duration |
|-----------|-------------|------------------|
| `tasks.load_pdf` | Extract text from PDF files | 2-5s per file |
| `tasks.split_documents` | Chunk text with overlap | 1-3s per document |

**When to use:** PDF uploads, document ingestion, text preprocessing

---

### 🧮 Vectorstore Queue
**Queue Name:** `vectorstore`  
**Worker:** `worker_vectorstore`  
**Concurrency:** 2 workers  
**Dependencies:** OpenAI API, ChromaDB, LangChain  
**Use Case:** Embedding generation and vector indexing

| Task Name | Description | Cost Impact |
|-----------|-------------|-------------|
| `tasks.create_vectorstore` | Generate embeddings and create vector index | High (OpenAI API calls) |

**When to use:** Initial document indexing, vectorstore creation, embedding updates

**⚠️ Note:** This queue makes OpenAI API calls. Monitor usage to control costs.

---

### 🤖 RAG Queue
**Queue Name:** `rag`  
**Worker:** `worker_rag`  
**Concurrency:** 2 workers  
**Dependencies:** OpenAI API, ChromaDB, LangChain  
**Use Case:** Real-time question answering and retrieval

| Task Name | Description | Response Time |
|-----------|-------------|---------------|
| `tasks.query_vectorstore` | Retrieve context and generate answers | 2-5s per query |

**When to use:** User queries, chatbot responses, semantic search

**⚠️ Note:** This queue makes OpenAI API calls. Consider rate limits and costs.

## 🎯 Task Routing

Tasks are automatically routed to their designated queues using Celery's task routing configuration.

### Configuration File
All routing rules are centralized in `src/core/queues.py`:

```python
TASK_ROUTES = {
    "tasks.process_data": "default",
    "tasks.add_numbers": "default",
    "tasks.divide_numbers": "default",
    "tasks.aggregate_results": "default",
    "tasks.load_pdf": "document",
    "tasks.split_documents": "document",
    "tasks.create_vectorstore": "vectorstore",
    "tasks.query_vectorstore": "rag",
}
```

### Usage in Code

```python
from src.core.queues import get_queue_for_task

# Get the appropriate queue for a task
queue = get_queue_for_task("tasks.add_numbers")  # Returns "default"

# Submit task to the queue
task = add_numbers_task.apply_async(args=[5, 10], queue=queue)
```

### Automatic Routing
Celery automatically routes tasks based on the configuration:

```python
# This task will automatically go to the "document" queue
load_pdf_task.apply_async(args=["/path/to/file.pdf"])
```

## 🚀 Deployment & Configuration

### Production (Docker Compose)

All workers are defined in `docker-compose.yml`. Start all services:

```bash
docker-compose up --build
```

Each worker runs as an independent container:

| Service | Container Name | Queue | Environment |
|---------|---------------|-------|-------------|
| `worker_default` | `rag_worker_default` | `default` | Redis URL |
| `worker_document` | `rag_worker_document` | `document` | Redis URL |
| `worker_vectorstore` | `rag_worker_vectorstore` | `vectorstore` | Redis URL, OpenAI API Key |
| `worker_rag` | `rag_worker_rag` | `rag` | Redis URL, OpenAI API Key |

### Local Development

**Option 1: Use helper scripts**
```bash
bash scripts/start_worker.sh default
bash scripts/start_worker.sh document
bash scripts/start_worker.sh vectorstore
bash scripts/start_worker.sh rag
```

**Option 2: Start manually**
```bash
# Terminal 1: Default worker
celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=info \
  --queues=default \
  --concurrency=2 \
  --hostname=worker_default@%h

# Terminal 2: Document worker
celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=info \
  --queues=document \
  --concurrency=2 \
  --hostname=worker_document@%h

# Terminal 3: Vectorstore worker
celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=info \
  --queues=vectorstore \
  --concurrency=2 \
  --hostname=worker_vectorstore@%h

# Terminal 4: RAG worker
celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=info \
  --queues=rag \
  --concurrency=2 \
  --hostname=worker_rag@%h
```

### Environment Variables

```bash
# Required for all workers
REDIS_URL=redis://localhost:6379/0

# Required for vectorstore and rag workers only
OPENAI_API_KEY=sk-...
```

## 📈 Scaling Strategies

### Horizontal Scaling (More Workers)

Scale specific queues based on demand:

```bash
# Scale RAG workers to handle more queries
docker-compose up --scale worker_rag=4

# Scale document workers during bulk uploads
docker-compose up --scale worker_document=3

# Scale all workers
docker-compose up \
  --scale worker_default=2 \
  --scale worker_document=3 \
  --scale worker_vectorstore=2 \
  --scale worker_rag=4
```

**When to scale horizontally:**
- High task queue length
- Increased request volume
- Multiple concurrent users

### Vertical Scaling (More Concurrency)

Increase concurrency per worker in `docker-compose.yml`:

```yaml
worker_rag:
  command: celery -A src.workers.celery_worker.celery_app worker \
    --loglevel=info \
    --queues=rag \
    --concurrency=4  # Increased from 2
    --hostname=worker_rag@%h
```

**When to scale vertically:**
- Workers have idle CPU
- I/O-bound tasks (waiting on API calls)
- Sufficient memory available

### Scaling Recommendations

| Queue | Typical Load | Recommended Scaling |
|-------|--------------|---------------------|
| `default` | Low | 1-2 workers, concurrency 2 |
| `document` | Medium (batch uploads) | 2-4 workers, concurrency 2-4 |
| `vectorstore` | Low (one-time indexing) | 1-2 workers, concurrency 2 |
| `rag` | High (user queries) | 3-5 workers, concurrency 4-8 |

## 📊 Monitoring & Observability

### API Endpoint: Queue Information

Get real-time information about queues and tasks:

```bash
curl http://localhost:8000/tasks/info
```

**Response:**
```json
{
  "queues": [
    {
      "name": "default",
      "description": "General purpose tasks (calculations, basic operations)"
    },
    {
      "name": "rag",
      "description": "RAG query tasks (question answering, retrieval)"
    },
    {
      "name": "document",
      "description": "Document processing tasks (PDF loading, text splitting)"
    },
    {
      "name": "vectorstore",
      "description": "Vector store operations (embedding creation, indexing)"
    }
  ],
  "tasks": [
    {"name": "tasks.process_data", "queue": "default"},
    {"name": "tasks.add_numbers", "queue": "default"},
    {"name": "tasks.divide_numbers", "queue": "default"},
    {"name": "tasks.aggregate_results", "queue": "default"},
    {"name": "tasks.load_pdf", "queue": "document"},
    {"name": "tasks.split_documents", "queue": "document"},
    {"name": "tasks.create_vectorstore", "queue": "vectorstore"},
    {"name": "tasks.query_vectorstore", "queue": "rag"}
  ]
}
```

### Flower Dashboard

**Access:** `http://localhost:5555`

**Features:**
- 📊 Real-time worker status
- 📈 Task execution metrics
- ⏱️ Task duration histograms
- 🔄 Queue length monitoring
- 💾 Worker resource usage (CPU, memory)
- 🔍 Task search and filtering
- 📝 Task result inspection

**Key Metrics to Monitor:**

| Metric | What to Watch | Action Threshold |
|--------|---------------|------------------|
| Queue Length | Tasks waiting to be processed | > 100 tasks: Scale workers |
| Task Success Rate | % of successful completions | < 95%: Investigate failures |
| Average Task Duration | Time per task | Increasing trend: Optimize code |
| Worker Utilization | % of time workers are busy | > 80%: Add workers |
| Failed Tasks | Number of failures | > 5%: Check logs |

### Logging

Workers log to stdout. View logs:

```bash
# Docker logs
docker logs rag_worker_default
docker logs rag_worker_rag -f  # Follow mode

# Filter by log level
docker logs rag_worker_rag 2>&1 | grep ERROR
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Redis health
docker exec rag_redis redis-cli ping

# Worker health (via Flower API)
curl http://localhost:5555/api/workers
```

## 💡 Best Practices

### Queue Selection Guidelines

```python
# ✅ Good: Use appropriate queue
load_pdf_task.apply_async(args=[pdf_path], queue="document")

# ❌ Bad: Wrong queue for task type
load_pdf_task.apply_async(args=[pdf_path], queue="default")

# ✅ Good: Use helper function
from src.core.queues import get_queue_for_task
queue = get_queue_for_task("tasks.load_pdf")
load_pdf_task.apply_async(args=[pdf_path], queue=queue)
```

### Error Handling

```python
# Configure retry logic for unreliable operations
@celery_app.task(name="tasks.api_call", bind=True, max_retries=3)
def api_call_task(self, data):
    try:
        return call_external_api(data)
    except APIError as exc:
        # Exponential backoff: 2^retries seconds
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
```

### Resource Management

```python
# Set task time limits to prevent hanging
celery_app.conf.update(
    task_time_limit=3600,      # Hard limit: 1 hour
    task_soft_time_limit=3300, # Soft limit: 55 minutes
)
```

### Cost Optimization

1. **Batch operations** - Group multiple embeddings into single API call
2. **Cache results** - Store frequently accessed data in Redis
3. **Rate limiting** - Control OpenAI API usage
4. **Queue prioritization** - Process critical tasks first

```python
# Example: Batch embedding creation
chunks_batch = [chunk1, chunk2, chunk3]  # Process multiple at once
embeddings = openai.Embedding.create(input=chunks_batch)
```

## 🔧 Troubleshooting

### Common Issues

#### Tasks Not Being Processed

**Symptoms:** Tasks stuck in "Pending" state

**Solutions:**
```bash
# 1. Check if workers are running
docker ps | grep worker

# 2. Check worker logs for errors
docker logs rag_worker_default

# 3. Verify Redis connection
docker exec rag_redis redis-cli ping

# 4. Check queue routing
curl http://localhost:8000/tasks/info
```

#### High Memory Usage

**Symptoms:** Workers consuming excessive memory

**Solutions:**
```yaml
# Limit tasks per worker in docker-compose.yml
command: celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=info \
  --queues=rag \
  --concurrency=2 \
  --max-tasks-per-child=100  # Restart worker after 100 tasks
```

#### Slow Task Execution

**Symptoms:** Tasks taking longer than expected

**Solutions:**
1. Check Flower dashboard for bottlenecks
2. Increase worker concurrency
3. Scale workers horizontally
4. Optimize task code
5. Add caching for repeated operations

#### OpenAI API Rate Limits

**Symptoms:** Tasks failing with rate limit errors

**Solutions:**
```python
# Add rate limiting to tasks
from celery import Task
from time import sleep

class RateLimitedTask(Task):
    def __call__(self, *args, **kwargs):
        sleep(0.1)  # 100ms delay between tasks
        return super().__call__(*args, **kwargs)

@celery_app.task(base=RateLimitedTask, name="tasks.query_vectorstore")
def query_vectorstore_task(question, persist_directory, top_k=3):
    # Task implementation
    pass
```

### Debug Mode

Enable verbose logging:

```bash
# Start worker with debug logging
celery -A src.workers.celery_worker.celery_app worker \
  --loglevel=debug \
  --queues=default
```

## 🚀 Advanced: Adding New Queues

### Step 1: Define Queue

Edit `src/core/queues.py`:

```python
# Add queue constant
QUEUE_EMAIL = "email"

# Add to available queues
AVAILABLE_QUEUES = [
    QUEUE_DEFAULT,
    QUEUE_RAG,
    QUEUE_DOCUMENT,
    QUEUE_VECTORSTORE,
    QUEUE_EMAIL,  # New queue
]

# Add description
QUEUE_DESCRIPTIONS = {
    # ... existing queues ...
    QUEUE_EMAIL: "Email notification tasks",
}

# Add task routing
TASK_ROUTES = {
    # ... existing routes ...
    "tasks.send_email": QUEUE_EMAIL,
}
```

### Step 2: Create Worker

Add to `docker-compose.yml`:

```yaml
worker_email:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: rag_worker_email
  command: celery -A src.workers.celery_worker.celery_app worker \
    --loglevel=info \
    --queues=email \
    --concurrency=4 \
    --hostname=worker_email@%h
  volumes:
    - ./storage:/app/storage
  environment:
    - REDIS_URL=redis://redis:6379/0
    - SMTP_HOST=${SMTP_HOST}
    - SMTP_PORT=${SMTP_PORT}
  depends_on:
    redis:
      condition: service_healthy
  restart: unless-stopped
```

### Step 3: Create Task

Create `src/tasks/email_tasks.py`:

```python
from src.core.celery_app import celery_app
import smtplib

@celery_app.task(name="tasks.send_email")
def send_email_task(to: str, subject: str, body: str):
    # Email sending logic
    return {"status": "sent", "to": to}
```

### Step 4: Deploy

```bash
# Rebuild and restart
docker-compose up --build

# Verify new queue
curl http://localhost:8000/tasks/info | jq '.queues[] | select(.name=="email")'
```

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🎯 Summary

This multi-queue architecture provides:

✅ **Isolation** - Tasks don't interfere with each other  
✅ **Scalability** - Scale queues independently  
✅ **Reliability** - Failures are contained  
✅ **Observability** - Monitor each queue separately  
✅ **Cost Control** - Optimize resource allocation  
✅ **Flexibility** - Easy to add new queues
