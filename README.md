<div align="center">

# Agora — Voice‑First Socratic Tutor

Multimodal tutoring with voice, retrieval‑augmented reasoning, and a collaborative whiteboard.

</div>

**Live stack:** FastAPI + LangGraph + Gemini + Qdrant + Next.js + Socket.IO + Deepgram + ElevenLabs

## Highlights

- Voice push‑to‑talk with real‑time STT and TTS
- Socratic prompting with frustration monitoring and quiz mode
- Materials ingest (PDF/images/text) into Qdrant RAG store
- Shared JSON schemas for tight frontend/backend contracts
- Interactive whiteboard actions (create notes, highlight, load images)
- Structured JSON logging and sane defaults for local/dev/prod

## Tech Stack

- Backend: FastAPI, LangGraph, Google Gemini, Qdrant, httpx, websockets
- Speech: Deepgram (STT), ElevenLabs (TTS), Piper/pyttsx3 (local fallback)
- Frontend: Next.js 16 (React 19), Tailwind, Zustand, socket.io‑client, Tldraw
- Data: Qdrant (vector DB), Docling (document parsing)
- Tooling: Pydantic v2, Ruff, MyPy, Vitest/Playwright (planned), Docker Compose

## Repository Layout

```
backend/                  # FastAPI app, services, LangGraph
	app/
		api/                  # HTTP + Socket.IO routes
		services/             # gemini, qdrant, stt, tts
		graph/                # state + nodes + builder
		workers/              # chunking + ingest
	requirements.txt        # Python deps (pip)
frontendOther/            # Next.js app (App Router)
	app/, components/, lib/ # UI, hooks, stores, ws client
shared/schema/            # Pydantic + Zod message contracts
docker-compose.yml        # Qdrant + (backend + frontend) services
.env.example              # Backend + Compose example env
```

## Environment

API keys are required. Copy examples and fill in values.

```zsh
cp .env.example .env                    # Backend + compose
cp frontendOther/.env.local.example frontendOther/.env.local  # Frontend
```

Required keys and sensible defaults are documented in the example files.

## Local Development

### Prereqs

- Python 3.11+
- Node.js 20+
- pnpm 9+ (Corepack auto‑installs) or npm
- Docker (for Qdrant/dev compose)

### 1) Start Qdrant

```zsh
docker compose up -d qdrant
```

### 2) Backend (FastAPI)

Option A — venv (recommended)
```zsh
cd backend
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.main
```

Option B — Conda
```zsh
cd backend
conda env create -f environment.yml
conda activate agora
python -m app.main
```

Backend serves at `http://localhost:8000` and mounts Socket.IO at `/socket.io`.

### 3) Frontend (Next.js)

```zsh
cd frontendOther
pnpm install
pnpm dev
```

Frontend runs at `http://localhost:3000`.

## Docker Deployment

We provide Dockerfiles for backend and frontend and extend `docker-compose.yml` to run the full stack.

Build and start everything:
```zsh
docker compose up -d --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Qdrant: http://localhost:6333

To follow logs:
```zsh
docker compose logs -f backend frontend qdrant
```

To stop:
```zsh
docker compose down
```

Notes:
- ElevenLabs is the default TTS in containers. Local Piper/pyttsx3 is supported but requires espeak-ng and lacks direct audio playback; we write to file and convert to MP3.
- Frontend `NEXT_PUBLIC_*` values are inlined at build time. Set them in `.env` (compose) or `frontendOther/.env.local` before building.

## Running Tests and Linters

Backend:
```zsh
cd backend
pytest
ruff check .
mypy .
```

Frontend:
```zsh
cd frontendOther
pnpm lint
pnpm build
```

## Key Features (Detail)

- Voice Loop: press‑to‑talk → STT → LangGraph route → RAG → Socratic response → TTS stream
- Materials Ingest: `/api/materials/upload` processes PDFs/images/text via Docling, embeds with Gemini, upserts to Qdrant per `user_id`/`course_id`
- Shared Contracts: JSON message types validated on both sides under `shared/schema`
- Whiteboard Actions: backend emits `visual` messages (create/hightlight/load) → Tldraw updates
- Session Tracking: uuidv4 `user_id` (localStorage) + `session_id` per run

## Troubleshooting

- Qdrant: `curl http://localhost:6333/health`
- WebSocket: ensure `NEXT_PUBLIC_WS_URL` points to `http://localhost:8000`
- STT/TTS: verify keys in `.env`; switch providers with `STT_PROVIDER`/`TTS_PROVIDER`
- Logs: set `LOG_LEVEL=INFO` to reduce noise; optional `LOG_FILE=/tmp/agora_backend.log`

## License

MIT — Built for NYU Hackathon 2025
