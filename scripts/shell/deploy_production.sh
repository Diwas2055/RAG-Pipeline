#!/bin/bash

# Production Deployment Script
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAG Pipeline - Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo -e "${RED}Error: .env.production file not found${NC}"
    echo -e "${YELLOW}Copy .env.production.example to .env.production and configure it${NC}"
    exit 1
fi

# Load production environment
export $(cat .env.production | grep -v '^#' | xargs)

# Check required variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env.production${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configuration loaded${NC}\n"

# Build images
echo -e "${BLUE}Building Docker images...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

echo -e "${GREEN}✓ Images built successfully${NC}\n"

# Stop existing containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

echo -e "${GREEN}✓ Containers stopped${NC}\n"

# Start services
echo -e "${BLUE}Starting production services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo -e "${GREEN}✓ Services started${NC}\n"

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 10

# Check API health
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    exit 1
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Prometheus health check failed${NC}"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Grafana health check failed${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Services:"
echo -e "  API:        http://localhost"
echo -e "  API Docs:   http://localhost/docs"
echo -e "  Flower:     http://localhost/flower"
echo -e "  Prometheus: http://localhost:9090"
echo -e "  Grafana:    http://localhost:3000 (admin/${GRAFANA_PASSWORD:-admin})"

echo -e "\n${YELLOW}View logs:${NC}"
echo -e "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"

echo -e "\n${YELLOW}Scale workers:${NC}"
echo -e "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker_rag=10"
