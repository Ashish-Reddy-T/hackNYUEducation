# Agora - Voice-first Socratic Tutor

A multimodal AI tutoring system that uses voice interaction, Socratic questioning, and visual aids to help students learn.

## Architecture

- **Backend**: FastAPI + LangGraph + Gemini 2.5 Pro + Qdrant
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS + Tldraw (in `frontendOther/`)
- **Services**: Deepgram (STT), ElevenLabs (TTS), Docling (document parsing)

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Conda (recommended)

### 1. Start Qdrant

```bash
docker-compose up -d
```

### 2. Setup Backend

```bash
cd backend

# Create conda environment
conda env create -f environment.yml
conda activate agora

# Copy environment variables
cp ../.env.example .env
# Edit .env with your API keys

# Run server
python -m app.main
```

The backend will be available at `http://localhost:8000`

### 3. Setup Frontend

```bash
cd frontendOther

# Install dependencies
pnpm install

# Frontend is pre-configured with .env.local

# Run dev server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## API Keys Required

- **Gemini API**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Deepgram API**: Get from [Deepgram](https://console.deepgram.com/)
- **ElevenLabs API**: Get from [ElevenLabs](https://elevenlabs.io/)

## Features

- ✅ Voice-first interaction (push-to-talk)
- ✅ Socratic tutoring methodology
- ✅ Document upload & parsing (PDF, images, text)
- ✅ RAG-based contextual responses
- ✅ Memory tracking of student progress
- ✅ Interactive whiteboard with Tldraw
- ✅ Real-time WebSocket communication
- ✅ Quiz generation from confused topics

## Project Structure

```
agora/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── services/     # Gemini, Qdrant, STT, TTS
│   │   ├── graph/        # LangGraph nodes and state
│   │   └── workers/      # Document processing
│   ├── environment.yml   # Conda dependencies
│   └── pyproject.toml    # Poetry config
├── frontend/
│   ├── src/
│   │   ├── routes/       # SvelteKit pages
│   │   ├── lib/          # Components, stores, services
│   │   └── app.html
│   └── package.json
├── shared/
│   └── schema/           # Shared type definitions
└── docker-compose.yml    # Qdrant service
```

## Development

### Backend

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Lint
ruff check .
mypy .
```

### Frontend

```bash
# Development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Lint
pnpm lint
```

## Logging

The application uses structured JSON logging with DEBUG level throughout. All logs include:
- Timestamp
- Log level
- Module/function name
- Context-specific metadata

Check backend logs for detailed execution traces.

## Troubleshooting

### Qdrant Connection Issues

Ensure Qdrant is running:
```bash
docker-compose ps
curl http://localhost:6333/health
```

### STT/TTS Errors

- Verify API keys in `.env`
- Check API rate limits
- Try fallback providers (whisper for STT, piper for TTS)

### WebSocket Disconnections

- Check CORS settings in `backend/app/main.py`
- Verify frontend is connecting to correct WebSocket URL
- Check browser console for errors

## License

MIT

## Contributors

Agora Team @ NYU Hackathon 2025
