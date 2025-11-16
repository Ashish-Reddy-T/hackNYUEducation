#!/bin/bash
# Quick start script - runs all services

set -e

echo "Starting Agora services..."

# Start Qdrant
echo "Starting Qdrant..."
docker-compose up -d

# Wait for Qdrant
echo "Waiting for Qdrant..."
for i in {1..10}; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo "✓ Qdrant ready"
        break
    fi
    sleep 1
done

# Start backend in background
echo "Starting backend..."
cd backend
conda run -n agora python -m app.main &
BACKEND_PID=$!
cd ..

echo "✓ Backend started (PID: $BACKEND_PID)"

# Give backend time to start
sleep 3

echo ""
echo "=================================="
echo "  Agora is running!"
echo "=================================="
echo ""
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Qdrant: http://localhost:6333"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID; docker-compose down; exit" INT
wait $BACKEND_PID
