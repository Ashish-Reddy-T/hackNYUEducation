# Testing Guide for Agora

## Overview

This guide covers testing the complete Agora system from backend services to frontend integration.

## Prerequisites

- All services running (see README.md)
- API keys configured in `.env`
- Qdrant running on localhost:6333

## Backend Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app_name": "Agora Backend",
  "version": "0.1.0",
  "services": {
    "qdrant": "healthy",
    "gemini": "healthy"
  }
}
```

### 2. Test Material Upload

```bash
# Create a test text file
echo "Mitosis is the process of cell division..." > test_note.txt

# Upload it
curl -X POST http://localhost:8000/api/materials/upload \
  -F "file=@test_note.txt" \
  -F "user_id=test-user-123" \
  -F "course_id=biology" \
  -F "description=Test biology notes"
```

Expected response:
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "message": "File uploaded successfully. Processing started."
}
```

### 3. Check Upload Status

```bash
curl http://localhost:8000/api/materials/status/{job_id}
```

### 4. List User Materials

```bash
curl "http://localhost:8000/api/materials/list?user_id=test-user-123&course_id=biology"
```

### 5. WebSocket Connection Test

Use a WebSocket client (e.g., wscat):

```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/ws/connect
```

Send initialization:
```json
{"type": "init_session", "user_id": "test-user", "course_id": "biology"}
```

Send text message:
```json
{"type": "text", "session_id": "session-123", "user_id": "test-user", "text": "What is mitosis?"}
```

## Integration Testing

### End-to-End Voice Loop Test

1. **Start all services**:
   ```bash
   ./start.sh
   ```

2. **Upload study materials**:
   - Go to `http://localhost:5173/materials`
   - Upload a PDF or text file
   - Wait for processing to complete

3. **Start voice session**:
   - Go to `http://localhost:5173`
   - Click "Start Session"
   - Hold the voice button and ask: "What is mitosis?"

4. **Verify flow**:
   - ✓ Audio recorded
   - ✓ Transcription appears
   - ✓ Tutor responds with Socratic question
   - ✓ Audio plays back
   - ✓ Conversation continues

### RAG Retrieval Test

1. Upload notes about a specific topic
2. Wait for processing
3. Ask a question about that topic
4. Check backend logs for:
   - Query embedding generation
   - Qdrant search results
   - Retrieved context being used in prompt

### Memory Tracking Test

1. Start a session
2. Discuss a topic multiple times
3. After 5 turns, check backend logs for memory update
4. Ask to be quizzed - should reference confused topics

## Frontend Component Testing

### RecorderButton

- Click and hold to record
- Release to stop
- Verify audio is captured
- Check console for debug logs

### TranscriptPanel

- Send multiple messages
- Verify student/tutor messages display correctly
- Check timestamps
- Verify scrolling behavior

### WhiteboardPane

- Wait for visual actions from backend
- Verify sticky notes appear
- Test drawing/erasing
- Test image loading

### OrbStatus

- Watch state transitions:
  - `idle` → Gray, still
  - `recording` → Red, pulsing
  - `thinking` → Blue, rotating
  - `speaking` → Green, pulsing

## Performance Testing

### Backend Response Times

Check logs for `processing_time_ms`:
- Target: < 2000ms for typical queries
- Target: < 500ms for cached responses

### Audio Latency

Measure end-to-end time:
- User speaks → STT → LangGraph → TTS → Audio plays
- Target: < 5 seconds total

### Qdrant Query Performance

Check Qdrant logs:
- Target: < 100ms per vector search
- Target: < 200ms for embedding generation

## Common Issues & Solutions

### Issue: "No relevant notes found"

**Solution**: 
- Verify materials were uploaded successfully
- Check Qdrant has documents: `curl http://localhost:6333/collections/agora_notes`
- Try more specific queries

### Issue: STT not transcribing

**Solution**:
- Check Deepgram API key
- Verify microphone permissions
- Check audio format compatibility
- Try Whisper fallback: Set `STT_PROVIDER=whisper` in .env

### Issue: TTS audio not playing

**Solution**:
- Check ElevenLabs API key
- Verify audio codec support in browser
- Check browser console for errors
- Test audio playback directly

### Issue: WebSocket disconnects

**Solution**:
- Check backend logs for errors
- Verify CORS settings
- Check network stability
- Increase timeout in wsClient.ts

### Issue: Qdrant connection failed

**Solution**:
- Verify Docker container running: `docker ps`
- Check port 6333 is not in use
- Restart Qdrant: `docker-compose restart`

## Debug Logging

All backend operations log extensively. Enable DEBUG level in `.env`:

```bash
LOG_LEVEL=DEBUG
```

Check logs for:
- `[Router]` - Routing decisions
- `[RAG]` - Context retrieval
- `[Socrates]` - Response generation
- `[Memory]` - Understanding tracking
- `[STT]` - Speech transcription
- `[TTS]` - Audio synthesis

## Automated Testing (Future)

### Backend Unit Tests

```bash
cd backend
conda activate agora
pytest tests/
```

### Frontend Unit Tests

```bash
cd frontend
pnpm test
```

### E2E Tests

```bash
cd frontend
pnpm test:e2e
```

## Load Testing

Use Locust or similar tools to test:
- Concurrent WebSocket connections
- Multiple file uploads
- Vector search throughput

## Success Criteria

✅ **Backend Health**: All services report healthy
✅ **Upload Pipeline**: Files processed within 30 seconds
✅ **Voice Loop**: End-to-end < 5 seconds
✅ **RAG Accuracy**: Retrieves relevant context 80%+ of time
✅ **Socratic Quality**: Asks questions, doesn't give direct answers
✅ **Memory Persistence**: Tracks progress across sessions
✅ **UI Responsiveness**: All interactions < 200ms perceived latency

## Monitoring

Watch logs in real-time:

```bash
# Backend logs (JSON format)
cd backend
tail -f agora.log | jq

# Docker logs
docker-compose logs -f qdrant
```

## Next Steps

1. Add automated test suite
2. Set up CI/CD pipeline
3. Add performance monitoring (Prometheus/Grafana)
4. Implement error tracking (Sentry)
5. Add user analytics
