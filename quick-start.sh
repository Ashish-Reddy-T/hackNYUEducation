#!/bin/bash

# Agora Quick Start Script
# Starts all services in the correct order

set -e

echo "🚀 Starting Agora System..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# 1. Start Qdrant
echo -e "${BLUE}[1/3]${NC} Starting Qdrant vector database..."
docker-compose up -d
sleep 2
echo -e "${GREEN}✅ Qdrant running on http://localhost:6333${NC}"
echo ""

# 2. Start Backend
echo -e "${BLUE}[2/3]${NC} Starting FastAPI backend..."
cd backend
/Users/AshishR_T/miniconda3/envs/agora/bin/python -m app.main > /tmp/agora_backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 4

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"
    echo "   PID: $BACKEND_PID"
    echo "   Logs: tail -f /tmp/agora_backend.log"
else
    echo -e "${YELLOW}⚠️  Backend may still be starting... check logs${NC}"
fi
echo ""

# 3. Start Frontend
echo -e "${BLUE}[3/3]${NC} Starting Next.js frontend..."
cd frontendOther
pnpm dev > /tmp/agora_frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

# Check if frontend started successfully
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend running on http://localhost:3000${NC}"
    echo "   PID: $FRONTEND_PID"
    echo "   Logs: tail -f /tmp/agora_frontend.log"
else
    echo -e "${YELLOW}⚠️  Frontend may still be starting... check logs${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Agora is now running!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Access Points:"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • Qdrant:    http://localhost:6333"
echo ""
echo "📋 Process IDs:"
echo "   • Backend:   $BACKEND_PID"
echo "   • Frontend:  $FRONTEND_PID"
echo ""
echo "📊 Monitor Logs:"
echo "   • Backend:   tail -f /tmp/agora_backend.log"
echo "   • Frontend:  tail -f /tmp/agora_frontend.log"
echo ""
echo "🛑 Stop Services:"
echo "   • Run: ./stop-all.sh"
echo "   • Or:  pkill -f 'python -m app.main' && pkill -f 'pnpm dev' && docker-compose down"
echo ""
echo "🧪 Test Upload:"
echo "   curl -X POST http://localhost:8000/api/materials/upload \\"
echo "     -F 'file=@your-file.pdf' \\"
echo "     -F 'user_id=test-user' \\"
echo "     -F 'course_id=test-course'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
