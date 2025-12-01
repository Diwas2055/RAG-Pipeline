#!/bin/bash

# Redis Cluster Setup Script
set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Redis Cluster Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if REDIS_PASSWORD is set
if [ -z "$REDIS_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  REDIS_PASSWORD not set in environment${NC}"
    echo -e "${YELLOW}Using default password: changeme${NC}"
    echo -e "${YELLOW}Set REDIS_PASSWORD in .env.production for production use${NC}\n"
    export REDIS_PASSWORD="changeme"
fi

# Stop existing cluster if running
echo -e "${BLUE}Stopping existing Redis cluster (if any)...${NC}"
docker-compose -f docker-compose.redis-cluster.yml down -v 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}\n"

# Start Redis nodes
echo -e "${BLUE}Starting Redis cluster nodes...${NC}"
docker-compose -f docker-compose.redis-cluster.yml up -d redis-node-1 redis-node-2 redis-node-3 redis-node-4 redis-node-5 redis-node-6

# Wait for nodes to be ready
echo -e "${BLUE}Waiting for nodes to be ready...${NC}"
sleep 10

# Initialize cluster
echo -e "${BLUE}Initializing Redis cluster...${NC}"
docker-compose -f docker-compose.redis-cluster.yml up redis-cluster-init

# Wait for cluster initialization
sleep 5

# Verify cluster status
echo -e "\n${BLUE}Verifying cluster status...${NC}"
docker exec redis-node-1 redis-cli -a "$REDIS_PASSWORD" --no-auth-warning cluster info

echo -e "\n${BLUE}Cluster nodes:${NC}"
docker exec redis-node-1 redis-cli -a "$REDIS_PASSWORD" --no-auth-warning cluster nodes

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Redis Cluster Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "Cluster Configuration:"
echo -e "  Nodes: 6 (3 masters, 3 replicas)"
echo -e "  Password: ${REDIS_PASSWORD}"
echo -e "  Ports: 7001-7006"
echo -e ""
echo -e "Connection String:"
echo -e "  ${YELLOW}redis://:${REDIS_PASSWORD}@localhost:7001,localhost:7002,localhost:7003${NC}"
echo -e ""
echo -e "Update .env.production:"
echo -e "  ${YELLOW}REDIS_URL=redis://:${REDIS_PASSWORD}@redis-node-1:6379${NC}"
echo -e ""
echo -e "Test connection:"
echo -e "  ${YELLOW}docker exec redis-node-1 redis-cli -a ${REDIS_PASSWORD} --no-auth-warning ping${NC}"
echo -e ""
echo -e "View cluster info:"
echo -e "  ${YELLOW}docker exec redis-node-1 redis-cli -a ${REDIS_PASSWORD} --no-auth-warning cluster info${NC}"
