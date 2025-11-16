# Backend Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies: ffmpeg for pydub, espeak-ng for pyttsx3 fallback
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       ffmpeg \
       espeak-ng libespeak-ng1 \
       libasound2 \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY backend /app

ENV HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
