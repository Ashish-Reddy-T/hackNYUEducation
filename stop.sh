#!/bin/bash
# Stop all Agora services

echo "Stopping Agora services..."

# Stop backend
pkill -f "python -m app.main" || true

# Stop Qdrant
docker-compose down

echo "All services stopped."
