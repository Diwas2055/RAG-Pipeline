# RAG Pipeline - Production Ready

**RAG pipelines** are everywhere now — powering chatbots, assistants, and enterprise search. Instead of revisiting what RAG is, let's talk about how to make it production-ready using one of the best approaches: leveraging **FastAPI**, **Celery**, and **Redis**, a trio that forms a distributed, asynchronous, and fault-tolerant architecture — unlike monolithic or sync-only setups, this design scales horizontally and stays responsive under heavy workloads. And this is where distributed tracing becomes key: it gives you visibility across API calls, background tasks, and caching layers, ensuring smooth debugging and performance tuning.

_A prior knowledge or understanding of **Python**, **LangChain**, and **Docker** will be helpful for setting up, customizing, and troubleshooting this pipeline._

A distributed trace is a collection of events, called "spans" that are linked together to show the end-to-end flow of a request.

## Components Overview

- **FastAPI**: The web framework that handles incoming requests, creating a new trace for each
- **Celery**: A distributed task queue system that allows you to run background tasks asynchronously
- **Redis**: An in-memory data structure store used as a message broker between FastAPI and Celery, and also as a caching layer
- **Flower**: A web-based tool for monitoring and administrating Celery clusters
- **LangChain**: Framework for building RAG applications
- **ChromaDB**: Vector database for storing embeddings
- **OpenAI**: Embeddings and LLM provider

## Architecture Overview

The architecture consists of FastAPI (handling API requests), Celery (processing background tasks), Redis (serving as both a message broker and cache), and Flower (monitoring Celery workers).

- **FastAPI** receives requests and delegates long-running or resource-intensive tasks to Celery via **Redis**
- **Celery** workers process these tasks in the background, so FastAPI can quickly respond to users without waiting for long-running operations to finish. Output from one task will be persisted in Redis cache for quick retrieval by subsequent tasks. Task status and results are also stored in Redis and can be queried by the FastAPI app
- **Flower** provides real-time monitoring of task execution and worker status
- **Docker** is used to containerize and orchestrate all components for consistent deployment

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   FastAPI   │─────▶│    Redis    │◀─────│   Celery    │
│     API     │      │   Broker    │      │   Workers   │
└─────────────┘      └─────────────┘      └─────────────┘
       │                                          │
       │                                          ▼
       ▼                                  ┌─────────────┐
┌─────────────┐                          │  RAG Tasks  │
│   Flower    │                          │  Processing │
│  Dashboard  │                          └─────────────┘
└─────────────┘

## Project Structure

```
.
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── routes/            # API endpoints
│   │   │   ├── tasks.py       # Basic task endpoints
│   │   │   └── rag.py         # RAG pipeline endpoints
│   │   ├── schemas.py         # Pydantic models
│   │   ├── dependencies.py    # Dependency injection
│   │   └── main.py           # FastAPI app initialization
│   ├── core/                  # Core configuration
│   │   ├── config.py         # Settings management
│   │   └── celery_app.py     # Celery configuration
│   ├── services/              # Business logic
│   │   ├── document_service.py    # PDF processing
│   │   ├── vectorstore_service.py # Vector operations
│   │   └── rag_service.py        # RAG query logic
│   ├── tasks/                 # Celery tasks
│   │   ├── basic_tasks.py    # Demo tasks
│   │   ├── document_tasks.py # Document processing
│   │   ├── vectorstore_tasks.py # Vector storage
│   │   └── rag_tasks.py      # RAG queries
│   └── workers/               # Worker configuration
│       └── celery_worker.py  # Worker entry point
├── scripts/                   # Utility scripts
├── tests/                     # Test suite
├── storage/                   # Data storage
│   ├── uploads/              # Uploaded files
│   └── vectorstores/         # Vector databases
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Container definition
├── requirements.txt          # Python dependencies
└── .env.example             # Environment template
```

## Step-by-Step Implementation

### Step 1: Install Dependencies

Refer `requirements.txt` for the full list of dependencies. Key packages include:
- `celery[redis]` - Distributed task queue
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - RAG framework
- `chromadb` - Vector database
- `openai` - LLM and embeddings

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Step 3: Define Celery Tasks

Let's first evaluate the main components using some basic tasks:

- `src/tasks/basic_tasks.py` - Sets up the Celery app and configures it to use Redis as the message broker. It also defines sample tasks `add_numbers_task` and `divide_numbers_task` that add and divide two numbers respectively
- `src/tasks/document_tasks.py` - Defines tasks for PDF reading and text splitting
- `src/tasks/vectorstore_tasks.py` - Defines tasks for creating vector embeddings
- `src/tasks/rag_tasks.py` - Defines tasks for querying the RAG system

### Step 4: Create FastAPI App

Let's create a FastAPI app that will send tasks to Celery workers and retrieve results:

- `src/api/main.py` - Sets up the FastAPI app and includes route modules
- `src/api/routes/tasks.py` - Defines endpoints to trigger Celery tasks:
  - `POST /tasks/calculate/add` - Add two numbers using Celery task (accepts JSON body)
  - `POST /tasks/calculate/divide` - Divide two numbers using Celery task (accepts JSON body)
  - `POST /tasks/workflow/chain` - Execute chained tasks (accepts JSON body)
  - `POST /tasks/workflow/parallel` - Execute parallel tasks (accepts JSON body)
  - `GET /tasks/status/{task_id}` - Get the result of a Celery task using its task ID
- `src/api/routes/rag.py` - Defines RAG pipeline endpoints

### Step 5: Dockerize the Application

Refer `Dockerfile` and `docker-compose.yml` for containerizing the FastAPI app, Celery workers, Redis, and Flower:

- `Dockerfile` - Defines the Docker image for the FastAPI app and Celery workers
- Register `worker_default` service in `docker-compose.yml` which will start a Celery worker process and listen to 'default' queue from Redis broker
- Register `worker_rag` service in `docker-compose.yml` which will start a Celery worker process and listen to 'rag' queue from Redis broker
- Register `flower` service in `docker-compose.yml` which will start Flower to monitor Celery workers
- Register `redis` service in `docker-compose.yml` which will start a Redis server
- Environment variables are used to configure Redis URL and OpenAI API key

### Step 6: Run the Application

**Quick Start (Using Makefile):**
```bash
# Setup and start everything
make quickstart

# Or individual commands
make install    # Install dependencies
make env        # Create .env file
make up         # Start all services
```

**Using Docker:**
```bash
docker-compose up --build
```

**Or run locally:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 1: Start API
make api
# or: bash scripts/start_api.sh

# Terminal 2: Start workers
make worker-rag
# or: bash scripts/start_worker.sh rag

# Terminal 3: Start Flower (optional)
make flower
```

**View all available commands:**
```bash
make help
```

**Access the services:**
- FastAPI at `http://localhost:8000`
- API Documentation at `http://localhost:8000/docs`
- Flower at `http://localhost:5555`

**Test the basic tasks:**

```bash
# Using Makefile
make test

# Or run scripts directly
bash scripts/test_tasks.sh      # Bash version
python scripts/test_tasks.py    # Python version
```

Or test manually with curl:
```bash
# Add two numbers
curl -X POST 'http://localhost:8000/tasks/calculate/add' \
  -H 'Content-Type: application/json' \
  -d '{"x": 5, "y": 10}'

# Response: {"task_id":"abc-123","status":"Task submitted"}

# Check task status
curl 'http://localhost:8000/tasks/status/abc-123'

# Divide numbers
curl -X POST 'http://localhost:8000/tasks/calculate/divide' \
  -H 'Content-Type: application/json' \
  -d '{"dividend": 20, "divisor": 4}'

# Chain workflow: add(5, 10) then divide by 3
curl -X POST 'http://localhost:8000/tasks/workflow/chain' \
  -H 'Content-Type: application/json' \
  -d '{"x": 5, "y": 10, "divisor": 3}'

# Parallel workflow: add(10, 5) + divide(10, 2) then sum results
curl -X POST 'http://localhost:8000/tasks/workflow/parallel' \
  -H 'Content-Type: application/json' \
  -d '{"x": 10, "y": 5, "z": 2}'
```

Result will be returned immediately with a task ID and initial status of `Task submitted`. Monitor the task status until it shows `Completed` and the result. Keep an eye on Flower dashboard to see task progress and worker status in real-time.

### Step 7: Extend to RAG Pipeline

Now that the basic setup is working, you can extend the Celery tasks to implement the RAG pipeline:

- `src/tasks/document_tasks.py` - Define Celery tasks for PDF reading and text splitting
- `src/tasks/vectorstore_tasks.py` - Define Celery tasks for vectorstore (ChromaDB) creation
- `src/tasks/rag_tasks.py` - Define Celery tasks for querying the vectorstore

**Place your PDF file:**
```bash
cp your_document.pdf storage/uploads/
```

**Execute the RAG pipeline:**
```bash
curl -X POST 'http://localhost:8000/rag/pipeline' \
  -H 'Content-Type: application/json' \
  -d '{
    "pdf_path": "/app/storage/uploads/your_document.pdf",
    "persist_directory": "/app/storage/vectorstores/my_docs"
  }'
```

This triggers the RAG pipeline tasks sequentially where output of one task is input to the next task.

## Deep Dive into RAG Tasks and Overall Flow

### 1. Configure Celery App

Configure a Celery app in `src/core/celery_app.py` to use Redis as the message broker. The configuration includes:
- Task serialization format
- Timezone settings
- Task result expiration
- Worker concurrency settings

### 2. Define Individual Celery Tasks

Individual Celery tasks for each step of the RAG pipeline:

- `load_pdf_task`: Reads and extracts text from the uploaded PDF file using PyPDF
- `split_documents_task`: Splits the extracted text into smaller chunks using LangChain's RecursiveCharacterTextSplitter
- `create_vectorstore_task`: Creates a Chroma vectorstore from the text chunks using OpenAI embeddings
- `query_vectorstore_task`: Queries the vectorstore and generates answers using RAG

### 3. How to Execute the Tasks

The `src/api/routes/rag.py` defines multiple ways to execute the tasks:

**Sequential Execution:**
The RAG pipeline endpoint executes tasks sequentially, where the output of one task is passed as input to the next:
- Uses `apply_async()` method to send each task to the Celery worker
- Uses `get()` method to wait for the result before proceeding to the next task
- Use `apply_async` when you want to execute tasks asynchronously and get a task ID immediately
- `apply_async()` accepts both positional and keyword arguments, plus additional options like passing `queue='rag'` to specify the queue

**Task Execution Patterns:**
- `delay()`: A shortcut to call a task asynchronously with default options. It is equivalent to `apply_async()` without any extra options
- `chain`: Use when you have a series of tasks that need to be executed in a specific order, where each task depends on the result of the previous one
- `group`: Use when you have multiple tasks that can run independently and you want to execute them in parallel, collecting all their results
- `chord`: Run a group of tasks in parallel and then execute a final callback task once all tasks in the group are complete, using their combined results

### 4. Configure Celery Workers to Listen to Different Queues

In `docker-compose.yml`, we define two Celery worker services:
- `worker_default` listens to the 'default' queue for basic tasks
- `worker_rag` listens to the 'rag' queue for RAG-specific tasks

This separation allows us to allocate resources and manage workloads effectively, ensuring that long-running RAG tasks do not block simpler tasks. Both workers are configured to use the same Redis broker for communication. Monitor the workers and tasks using Flower at `http://localhost:5555`.

Using different queues helps in prioritizing tasks and scaling specific parts of the application as needed.

### 5. How to Trigger the Workflow

**Query the RAG system:**
```bash
curl -X POST 'http://localhost:8000/rag/query/sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What is the main topic of this document?",
    "persist_directory": "/app/storage/vectorstores/my_docs",
    "top_k": 3
  }'
```

**Python Client Example:**
```python
import requests

# Process document
response = requests.post(
    "http://localhost:8000/rag/pipeline",
    json={
        "pdf_path": "/app/storage/uploads/doc.pdf",
        "persist_directory": "/app/storage/vectorstores/docs"
    }
)
task_ids = response.json()["task_ids"]

# Query document
response = requests.post(
    "http://localhost:8000/rag/query/sync",
    json={
        "question": "Summarize the document",
        "persist_directory": "/app/storage/vectorstores/docs"
    }
)
answer = response.json()["answer"]
print(answer)
```

## Queue Architecture

The system uses **4 specialized queues** for optimal task distribution:

| Queue | Purpose | Worker | Tasks |
|-------|---------|--------|-------|
| `default` | General operations | `worker_default` | Basic calculations, data processing |
| `document` | Document processing | `worker_document` | PDF loading, text splitting |
| `vectorstore` | Vector operations | `worker_vectorstore` | Embedding creation, indexing |
| `rag` | RAG queries | `worker_rag` | Question answering, retrieval |

Tasks are automatically routed to the appropriate queue based on their type. This separation allows:
- Independent scaling of workers per queue
- Resource isolation (e.g., OpenAI API calls only in specific workers)
- Better monitoring and debugging
- Prioritization of critical tasks

View queue and task information:
```bash
curl http://localhost:8000/tasks/info
```

## API Endpoints

### Task Management
- `GET /tasks/info` - List available queues and registered tasks
- `POST /tasks/process` - Start background task (body: `{"data": "string"}`)
- `GET /tasks/status/{task_id}` - Check task status
- `POST /tasks/calculate/add` - Add numbers (body: `{"x": int, "y": int}`)
- `POST /tasks/calculate/divide` - Divide numbers (body: `{"dividend": int, "divisor": int}`)
- `POST /tasks/workflow/chain` - Task chain: add then divide (body: `{"x": int, "y": int, "divisor": int}`)
- `POST /tasks/workflow/parallel` - Parallel tasks with aggregation (body: `{"x": int, "y": int, "z": int}`)

### RAG Pipeline
- `POST /rag/pipeline` - Process PDF through RAG pipeline
- `POST /rag/query` - Query vectorstore (async)
- `POST /rag/query/sync` - Query vectorstore (sync)

## Configuration

Key environment variables in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379/0

# Optional (with defaults)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
LLM_MODEL=gpt-3.5-turbo
RETRIEVAL_TOP_K=3
```

## Monitoring

Access Flower dashboard at http://localhost:5555 to monitor:
- Active workers
- Task execution status
- Task history
- Worker resource usage

## Production Deployment

### Quick Production Setup

**1. Generate Secure Keys:**
```bash
make keys
# Copy generated keys to .env.production
```

**2. Configure Environment:**
```bash
cp .env.production.example .env.production
# Edit with your production values and generated keys
```

**3. Deploy:**
```bash
make prod
# or: bash scripts/deploy_production.sh
```

**4. Setup Redis Cluster (Optional):**
```bash
make redis-cluster
```

**3. Access Services:**
- API: http://localhost (with Nginx)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Production Features

#### 🔐 Authentication
API key authentication protects your endpoints:

```bash
# Configure in .env.production
API_KEYS=key1,key2,key3
ENABLE_AUTH=true

# Use in requests
curl -H "X-API-Key: key1" http://localhost/rag/query
```

#### ⚡ Rate Limiting
Two-level rate limiting prevents abuse:
- **Nginx**: 60 req/min (general), 20 req/min (RAG queries)
- **Redis**: Application-level rate limiting per client IP

#### 📊 Monitoring
Prometheus + Grafana for metrics:
- Request rate and latency
- Error rates
- Worker status
- Queue lengths

```bash
# View metrics
curl http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])
```

#### 📝 Structured Logging
JSON logging for better observability:

```bash
# Enable in .env.production
LOG_LEVEL=INFO
LOG_FORMAT=json

# View logs
docker logs rag_api -f
```

#### 🔄 Reverse Proxy
Nginx provides:
- Load balancing across API instances
- SSL/TLS termination
- Security headers
- Request logging

#### 📈 Scaling

**Horizontal Scaling:**
```bash
# Scale workers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d \
  --scale worker_rag=10 \
  --scale worker_document=5
```

**Vertical Scaling:**
Edit `docker-compose.prod.yml`:
```yaml
worker_rag:
  command: celery ... --concurrency=8  # Increase from 2
```

### Production Checklist

- [ ] Configure `.env.production` with secure values
- [ ] Set up SSL/TLS certificates (Let's Encrypt or self-signed)
- [ ] Configure API keys for authentication
- [ ] Set up Grafana dashboards
- [ ] Configure log aggregation (optional: ELK Stack)
- [ ] Set up backup automation for Redis and vector stores
- [ ] Configure firewall rules
- [ ] Enable Redis authentication (optional)
- [ ] Set up alerting (PagerDuty, Slack)

### Detailed Guides

- **[Production Deployment Guide](docs/production-deployment.md)** - Comprehensive production setup
- **[Queue System Guide](docs/queue-system-guide.md)** - Multi-queue architecture details

## Troubleshooting

**Workers not picking up tasks?**
- Check Redis connection
- Verify queue names match
- Check Flower dashboard for worker status

**Out of memory errors?**
- Reduce chunk size
- Limit concurrent workers
- Increase worker memory limits

**Slow query responses?**
- Reduce `top_k` value
- Optimize chunk size
- Use faster embedding model

## License

MIT License - See LICENSE file for details
