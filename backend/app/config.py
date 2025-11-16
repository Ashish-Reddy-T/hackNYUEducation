"""
Configuration management for Agora backend using Pydantic Settings.
Loads environment variables and provides validated configuration.
"""
import logging
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Agora Backend"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "DEBUG"
    log_file: str | None = Field(default=None, description="Path to log file")
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # API Keys
    gemini_api_key: str = Field(alias="GEMINI_API")
    deepgram_api_key: str = Field(alias="DEEPGRAM_API")
    elevenlabs_api_key: str = Field(alias="ELEVEN_API")
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_notes: str = "agora_notes"
    qdrant_collection_memory: str = "agora_memory"
    qdrant_vector_size: int = 768  # Gemini embedding dimension
    
    # STT Configuration
    stt_provider: Literal["deepgram", "whisper"] = "deepgram"
    whisper_model: str = "base"  # tiny, base, small, medium, large
    
    # TTS Configuration
    tts_provider: Literal["elevenlabs", "piper"] = "elevenlabs"
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    elevenlabs_model: str = "eleven_turbo_v2"
    
    # Storage
    storage_path: Path = Field(default=Path("backend/storage"))
    upload_max_size: int = 50 * 1024 * 1024  # 50MB
    
    # LangGraph & LLM
    gemini_model: str = "gemini-2.5-pro"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048
    
    # Session & Memory
    session_timeout: int = 3600  # 1 hour
    memory_update_interval: int = 5  # Update memory every N turns
    frustration_threshold: int = 3  # Frustration level to trigger mode change
    
    # Feature Flags
    enable_quiz_mode: bool = True
    enable_visual_actions: bool = True
    enable_frustration_monitor: bool = True
    enable_self_explanation: bool = False  # Advanced feature
    
    @field_validator("storage_path")
    @classmethod
    def create_storage_path(cls, v: Path) -> Path:
        """Ensure storage directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Storage path validated: {v}")
        return v
    
    @field_validator("gemini_api_key", "deepgram_api_key", "elevenlabs_api_key")
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        """Validate API keys are not empty."""
        if not v or v.strip() == "":
            field_name = info.field_name
            logger.error(f"API key validation failed: {field_name} is empty")
            raise ValueError(f"{field_name} cannot be empty")
        logger.debug(f"API key validated: {info.field_name}")
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Settings initialized", extra={
            "app_name": self.app_name,
            "debug": self.debug,
            "stt_provider": self.stt_provider,
            "tts_provider": self.tts_provider,
            "qdrant_url": self.qdrant_url,
            "gemini_model": self.gemini_model
        })


# Global settings instance
settings = Settings()

logger.info("Configuration loaded successfully", extra={
    "config_source": ".env",
    "log_level": settings.log_level,
    "feature_flags": {
        "quiz_mode": settings.enable_quiz_mode,
        "visual_actions": settings.enable_visual_actions,
        "frustration_monitor": settings.enable_frustration_monitor
    }
})
