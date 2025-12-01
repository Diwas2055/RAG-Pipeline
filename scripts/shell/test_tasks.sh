#!/bin/bash

# Task Management API Testing Script
# This script tests all task management endpoints

BASE_URL="http://localhost:8000"
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Task Management API Testing${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to check task status
check_task_status() {
    local task_id=$1
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo -e "${YELLOW}Checking status (attempt $attempt/$max_attempts)...${NC}"
        response=$(curl -s "${BASE_URL}/tasks/status/${task_id}")
        status=$(echo $response | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        
        if [ "$status" = "Completed" ]; then
            echo -e "${GREEN}✓ Task completed!${NC}"
            echo -e "Result: $response\n"
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    echo -e "${YELLOW}Task still pending after $max_attempts attempts${NC}\n"
    return 1
}

# Test 1: Process Data
echo -e "${BLUE}Test 1: Process Data${NC}"
echo "POST /tasks/process"
response=$(curl -s -X POST "${BASE_URL}/tasks/process" \
  -H "Content-Type: application/json" \
  -d '{"data": "test data"}')
echo "Response: $response"
task_id=$(echo $response | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$task_id" ]; then
    check_task_status "$task_id"
fi

# Test 2: Add Numbers
echo -e "${BLUE}Test 2: Add Numbers${NC}"
echo "POST /tasks/calculate/add"
response=$(curl -s -X POST "${BASE_URL}/tasks/calculate/add" \
  -H "Content-Type: application/json" \
  -d '{"x": 15, "y": 25}')
echo "Response: $response"
task_id=$(echo $response | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$task_id" ]; then
    check_task_status "$task_id"
fi

# Test 3: Divide Numbers
echo -e "${BLUE}Test 3: Divide Numbers${NC}"
echo "POST /tasks/calculate/divide"
response=$(curl -s -X POST "${BASE_URL}/tasks/calculate/divide" \
  -H "Content-Type: application/json" \
  -d '{"dividend": 100, "divisor": 5}')
echo "Response: $response"
task_id=$(echo $response | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$task_id" ]; then
    check_task_status "$task_id"
fi

# Test 4: Chain Workflow
echo -e "${BLUE}Test 4: Chain Workflow (add then divide)${NC}"
echo "POST /tasks/workflow/chain"
echo "Operation: (10 + 20) / 5 = 6"
response=$(curl -s -X POST "${BASE_URL}/tasks/workflow/chain" \
  -H "Content-Type: application/json" \
  -d '{"x": 10, "y": 20, "divisor": 5}')
echo "Response: $response"
task_id=$(echo $response | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$task_id" ]; then
    check_task_status "$task_id"
fi

# Test 5: Parallel Workflow
echo -e "${BLUE}Test 5: Parallel Workflow (add + divide, then sum)${NC}"
echo "POST /tasks/workflow/parallel"
echo "Operation: (10 + 5) + (10 / 2) = 15 + 5 = 20"
response=$(curl -s -X POST "${BASE_URL}/tasks/workflow/parallel" \
  -H "Content-Type: application/json" \
  -d '{"x": 10, "y": 5, "z": 2}')
echo "Response: $response"
task_id=$(echo $response | grep -o '"task_id":"[^"]*"' | cut -d'"' -f4)
if [ ! -z "$task_id" ]; then
    check_task_status "$task_id"
fi

# Test 6: Task Info (Queues and Tasks)
echo -e "${BLUE}Test 6: Task Info (Available Queues and Tasks)${NC}"
echo "GET /tasks/info"
response=$(curl -s "${BASE_URL}/tasks/info")
echo -e "Response: $response\n"

# Test 7: Health Check
echo -e "${BLUE}Test 7: Health Check${NC}"
echo "GET /health"
response=$(curl -s "${BASE_URL}/health")
echo -e "Response: $response\n"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nView Flower dashboard at: http://localhost:5555"
echo -e "View API docs at: ${BASE_URL}/docs"
