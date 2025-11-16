# Agora Development Cheat Sheet

## Quick Commands

### Start Everything
```bash
./quick-start.sh
```

### Stop Everything
```bash
./stop-all.sh
```

### Individual Service Control

**Qdrant:**
```bash
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose logs -f    # View logs
```

**Backend:**
```bash
cd backend
conda activate agora
python -m app.main        # Start in foreground
# OR background:
/Users/AshishR_T/miniconda3/envs/agora/bin/python -m app.main > /tmp/agora_backend.log 2>&1 &
```

**Frontend:**
```bash
cd frontendOther
pnpm dev                  # Start in foreground
# OR background:
pnpm dev > /tmp/agora_frontend.log 2>&1 &
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Materials
```bash
curl -X POST http://localhost:8000/api/materials/upload \
  -F "file=@document.pdf" \
  -F "user_id=user-123" \
  -F "course_id=biology-101"
```

### Check Upload Status
```bash
curl http://localhost:8000/api/materials/status/{job_id}
```

### List Materials
```bash
curl "http://localhost:8000/api/materials/list?user_id=user-123"
```

### WebSocket Connection
```javascript
// Frontend (already integrated in frontendOther)
const socket = io('http://localhost:8000');
socket.emit('audio', {
  type: 'audio',
  session_id: 'session-id',
  user_id: 'user-id',
  format: 'audio/webm',
  data: base64AudioData
});
```

## Debugging

### View Logs
```bash
# Backend logs (JSON format)
tail -f /tmp/agora_backend.log | jq .

# Frontend logs
tail -f /tmp/agora_frontend.log

# Qdrant logs
docker-compose logs -f qdrant
```

### Check Processes
```bash
# Find backend process
ps aux | grep "python -m app.main"

# Find frontend process
ps aux | grep "pnpm dev"

# Check Qdrant
docker ps | grep qdrant
```

### Check Ports
```bash
# Check if ports are in use
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :6333  # Qdrant
```

## Testing

### Test Backend Health
```bash
curl -s http://localhost:8000/health | jq .
```

### Test Upload Pipeline
```bash
# Create test file
echo "Test content" > /tmp/test.txt

# Upload
JOB_ID=$(curl -s -X POST http://localhost:8000/api/materials/upload \
  -F "file=@/tmp/test.txt" \
  -F "user_id=test" \
  -F "course_id=test" | jq -r .job_id)

# Wait and check status
sleep 10
curl -s "http://localhost:8000/api/materials/status/$JOB_ID" | jq .
```

### Test Frontend
```bash
# Check if frontend is responding
curl -I http://localhost:3000
```

### Test WebSocket (with wscat)
```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/ws/connect
# Then send:
{"type": "text", "session_id": "test", "user_id": "test", "text": "Hello"}
```

## Common Issues

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
# Kill if needed
kill -9 <PID>

# Check conda environment
conda env list | grep agora
conda activate agora

# Check API keys
cat .env | grep -E "GEMINI|DEEPGRAM|ELEVEN"
```

### Frontend won't start
```bash
# Check if port 3000 is in use
lsof -i :3000
kill -9 <PID>

# Reinstall dependencies
cd frontendOther
rm -rf node_modules .next
pnpm install
```

### Qdrant issues
```bash
# Restart Qdrant
docker-compose down
docker-compose up -d

# Check status
curl http://localhost:6333
```

### Upload fails
```bash
# Check Qdrant connection
curl http://localhost:6333

# Check Gemini API key
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv('.env')
print(f"GEMINI_API: {os.getenv('GEMINI_API')[:10]}...")
EOF

# Check backend logs for errors
tail -50 /tmp/agora_backend.log | grep -i error
```

## File Locations

### Backend
- Main app: `backend/app/main.py`
- Config: `backend/app/config.py`
- API routes: `backend/app/api/`
- LangGraph nodes: `backend/app/graph/nodes/`
- Services: `backend/app/services/`
- Workers: `backend/app/workers/`

### Frontend
- Main page: `frontendOther/app/page.tsx`
- Components: `frontendOther/components/`
- Services: `frontendOther/lib/services/`
- Stores: `frontendOther/lib/store/`
- Types: `frontendOther/lib/types/`

### Configuration
- Backend env: `backend/.env`
- Frontend env: `frontendOther/.env.local`
- Root env: `.env`
- Docker: `docker-compose.yml`

### Logs
- Backend: `/tmp/agora_backend.log`
- Frontend: `/tmp/agora_frontend.log`

### Storage
- Uploaded files: `backend/storage/{user_id}/{course_id}/`
- Qdrant data: `./qdrant_storage/` (Docker volume)

## Environment Variables

### Backend (.env)
```bash
GEMINI_API=your_key_here
DEEPGRAM_API=your_key_here
ELEVEN_API=your_key_here
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=http://localhost:8000
NEXT_PUBLIC_DEBUG=true
```

## Development Workflow

### Making Backend Changes
```bash
# 1. Edit code in backend/app/
# 2. Stop backend
pkill -f "python -m app.main"
# 3. Restart (auto-reload not enabled by default)
cd backend && python -m app.main
```

### Making Frontend Changes
```bash
# 1. Edit code in frontendOther/
# 2. Changes auto-reload (Turbopack)
# 3. If needed, restart:
pkill -f "pnpm dev"
cd frontendOther && pnpm dev
```

### Testing Changes
```bash
# 1. Check logs
tail -f /tmp/agora_backend.log | jq .

# 2. Test endpoint
curl http://localhost:8000/health

# 3. Check frontend
open http://localhost:3000
```

## Useful Commands

### Clean Everything
```bash
# Stop all services
./stop-all.sh

# Clean Python cache
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Clean frontend build
rm -rf frontendOther/.next

# Clean Qdrant data (WARNING: deletes all vectors)
docker-compose down -v
```

### Reset Database
```bash
# Stop Qdrant
docker-compose down -v

# Restart (creates fresh collections)
docker-compose up -d
```

### Export Logs
```bash
# Export backend logs from last hour
tail -1000 /tmp/agora_backend.log > backend_logs_$(date +%Y%m%d_%H%M%S).json

# Export with timestamp filter
grep "2025-11-16" /tmp/agora_backend.log > logs_today.json
```

### Monitor Resources
```bash
# Watch processes
watch -n 1 'ps aux | grep -E "python|pnpm|docker" | grep -v grep'

# Monitor ports
watch -n 1 'lsof -i :8000 -i :3000 -i :6333'
```

## Performance Tips

### Backend
- Use `uvicorn --workers 4` for production
- Enable response caching for frequent queries
- Batch Qdrant operations
- Monitor memory usage with `top` or `htop`

### Frontend
- Build for production: `pnpm build && pnpm start`
- Use Next.js Image component for optimized images
- Implement lazy loading for components

### Qdrant
- Adjust `m` and `ef_construct` for HNSW index
- Use batch uploads for multiple documents
- Monitor disk usage: `du -sh qdrant_storage/`

## Keyboard Shortcuts

### Browser (Frontend)
- `Cmd+Shift+I` - Open DevTools
- `Cmd+Shift+C` - Inspect element
- `Cmd+Option+J` - Console

### Terminal
- `Ctrl+C` - Stop foreground process
- `Ctrl+Z` - Suspend process
- `fg` - Resume suspended process
- `jobs` - List background jobs

## URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main UI |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | OpenAPI/Swagger |
| Qdrant | http://localhost:6333 | Vector DB |
| Qdrant UI | http://localhost:6333/dashboard | Web interface |

## Documentation

- `README.md` - Project overview & quick start
- `TEST_RESULTS.md` - Integration test results
- `TESTING.md` - Comprehensive testing guide
- `PROJECT_SUMMARY.md` - Architecture & implementation details
- `AGENTS.md` - Repository guidelines
- `CHEATSHEET.md` - This file
