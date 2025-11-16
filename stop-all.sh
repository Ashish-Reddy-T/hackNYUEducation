#!/bin/bash

# Agora Stop All Services Script

echo "🛑 Stopping Agora services..."
echo ""

# Stop Backend
echo "[1/3] Stopping FastAPI backend..."
pkill -f "python -m app.main" 2>/dev/null && echo "✅ Backend stopped" || echo "⚠️  Backend was not running"

# Stop Frontend
echo "[2/3] Stopping Next.js frontend..."
pkill -f "pnpm dev" 2>/dev/null && echo "✅ Frontend stopped" || echo "⚠️  Frontend was not running"

# Stop Qdrant
echo "[3/3] Stopping Qdrant..."
docker-compose down 2>/dev/null && echo "✅ Qdrant stopped" || echo "⚠️  Qdrant was not running"

echo ""
echo "✅ All Agora services stopped"
