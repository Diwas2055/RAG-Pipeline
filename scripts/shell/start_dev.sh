#!/bin/bash

echo "Starting RAG Pipeline in Development Mode..."

# Create storage directories
mkdir -p storage/uploads storage/vectorstores

# Start services
docker-compose up --build
