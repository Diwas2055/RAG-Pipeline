.PHONY: help install dev prod test clean keys redis-cluster

# Default target
help:
	@echo "RAG Pipeline - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make keys             - Generate secure API keys"
	@echo "  make env              - Create .env file from example"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start development environment"
	@echo "  make api              - Start API server locally"
	@echo "  make worker           - Start default worker locally"
	@echo "  make worker-rag       - Start RAG worker locally"
	@echo "  make worker-document  - Start document worker locally"
	@echo "  make worker-vectorstore - Start vectorstore worker locally"
	@echo "  make flower           - Start Flower monitoring"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run test scripts"
	@echo "  make test-bash        - Run bash test script"
	@echo "  make test-python      - Run Python test script"
	@echo ""
	@echo "Production:"
	@echo "  make prod             - Deploy production environment"
	@echo "  make redis-cluster    - Setup Redis cluster"
	@echo "  make scale-rag        - Scale RAG workers (default: 5)"
	@echo "  make scale-document   - Scale document workers (default: 3)"
	@echo ""
	@echo "Docker:"
	@echo "  make up               - Start all services"
	@echo "  make down             - Stop all services"
	@echo "  make build            - Build Docker images"
	@echo "  make logs             - View logs"
	@echo "  make ps               - List running containers"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            - Clean up containers and volumes"
	@echo "  make clean-all        - Clean everything including images"
	@echo "  make backup-redis     - Backup Redis data"
	@echo "  make backup-vectors   - Backup vector stores"
	@echo ""

# Setup & Installation
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

keys:
	@echo "Generating secure API keys..."
	python scripts/python/generate_api_keys.py

env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		cp .env.example .env; \
		echo "✓ Created .env file. Please edit it with your configuration."; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Development
dev:
	@echo "Starting development environment..."
	bash scripts/shell/start_dev.sh

api:
	@echo "Starting API server..."
	bash scripts/shell/start_api.sh

worker:
	@echo "Starting default worker..."
	bash scripts/shell/start_worker.sh default

worker-rag:
	@echo "Starting RAG worker..."
	bash scripts/shell/start_worker.sh rag

worker-document:
	@echo "Starting document worker..."
	bash scripts/shell/start_worker.sh document

worker-vectorstore:
	@echo "Starting vectorstore worker..."
	bash scripts/shell/start_worker.sh vectorstore

flower:
	@echo "Starting Flower monitoring..."
	celery -A src.workers.celery_worker.celery_app flower

# Testing
test: test-python

test-bash:
	@echo "Running bash test script..."
	bash scripts/shell/test_tasks.sh

test-python:
	@echo "Running Python test script..."
	python scripts/python/test_tasks.py

# Production
prod:
	@echo "Deploying production environment..."
	bash scripts/shell/deploy_production.sh

redis-cluster:
	@echo "Setting up Redis cluster..."
	bash scripts/shell/setup_redis_cluster.sh

scale-rag:
	@echo "Scaling RAG workers to 5..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker_rag=5

scale-document:
	@echo "Scaling document workers to 3..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker_document=3

# Docker
up:
	@echo "Starting all services..."
	docker-compose up -d

down:
	@echo "Stopping all services..."
	docker-compose down

build:
	@echo "Building Docker images..."
	docker-compose build

logs:
	@echo "Viewing logs (Ctrl+C to exit)..."
	docker-compose logs -f

logs-api:
	@echo "Viewing API logs..."
	docker logs rag_api -f

logs-worker:
	@echo "Viewing worker logs..."
	docker logs rag_worker_rag -f

ps:
	@echo "Listing running containers..."
	docker-compose ps

# Maintenance
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "✓ Cleanup complete"

clean-all: clean
	@echo "Removing Docker images..."
	docker-compose down -v --rmi all
	@echo "✓ Full cleanup complete"

backup-redis:
	@echo "Backing up Redis data..."
	@mkdir -p backups
	docker exec rag_redis redis-cli SAVE
	docker cp rag_redis:/data/dump.rdb backups/redis-$$(date +%Y%m%d-%H%M%S).rdb
	@echo "✓ Redis backup complete"

backup-vectors:
	@echo "Backing up vector stores..."
	@mkdir -p backups
	tar -czf backups/vectorstores-$$(date +%Y%m%d-%H%M%S).tar.gz storage/vectorstores/
	@echo "✓ Vector stores backup complete"

# Health checks
health:
	@echo "Checking service health..."
	@echo -n "API: "
	@curl -s http://localhost:8000/health | grep -q "healthy" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Redis: "
	@docker exec rag_redis redis-cli ping 2>/dev/null | grep -q "PONG" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Prometheus: "
	@curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Prometheus" && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Grafana: "
	@curl -s http://localhost:3000/api/health 2>/dev/null | grep -q "ok" && echo "✓ Healthy" || echo "✗ Unhealthy"

# Quick start
quickstart: env install up
	@echo ""
	@echo "✓ Quick start complete!"
	@echo ""
	@echo "Services:"
	@echo "  API:    http://localhost:8000"
	@echo "  Docs:   http://localhost:8000/docs"
	@echo "  Flower: http://localhost:5555"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your OPENAI_API_KEY"
	@echo "  2. Run 'make test' to verify setup"
