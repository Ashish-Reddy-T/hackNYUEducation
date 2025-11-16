"""
Text-to-Speech (TTS) service with pluggable providers.
Supports ElevenLabs API and local Piper.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the TTS engine."""
        pass
    
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Input text
        
        Returns:
            Audio bytes (typically MP3 or WAV)
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup resources."""
        pass


class ElevenLabsTTS(TTSEngine):
    """ElevenLabs API TTS implementation."""
    
    def __init__(self):
        """Initialize ElevenLabs TTS."""
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
        self.model = settings.elevenlabs_model
        self.client = None
        
        logger.debug("ElevenLabsTTS instantiated", extra={
            "voice_id": self.voice_id,
            "model": self.model
        })
    
    async def initialize(self) -> None:
        """Initialize ElevenLabs client."""
        try:
            logger.debug("Initializing ElevenLabs client...")
            
            from elevenlabs import ElevenLabs
            
            self.client = ElevenLabs(api_key=self.api_key)
            
            logger.info("ElevenLabs TTS initialized successfully", extra={
                "voice_id": self.voice_id,
                "model": self.model
            })
            
        except Exception as e:
            logger.error("Failed to initialize ElevenLabs", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech using ElevenLabs.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (MP3)
        """
        try:
            logger.debug("Synthesizing with ElevenLabs", extra={
                "text_length": len(text),
                "voice_id": self.voice_id
            })
            
            if not self.client:
                raise RuntimeError("ElevenLabs client not initialized")
            
            logger.debug("Calling ElevenLabs API...")
            
            # Generate audio
            audio_generator = self.client.generate(
                text=text,
                voice=self.voice_id,
                model=self.model
            )
            
            # Collect audio chunks
            audio_chunks = []
            for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            audio_data = b"".join(audio_chunks)
            
            logger.info("ElevenLabs synthesis completed", extra={
                "text_length": len(text),
                "audio_size": len(audio_data)
            })
            
            return audio_data
            
        except Exception as e:
            logger.error("ElevenLabs synthesis failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(text)
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close ElevenLabs client."""
        logger.debug("Closing ElevenLabs client...")
        self.client = None
        logger.info("ElevenLabs client closed")


class PiperTTS(TTSEngine):
    """Local Piper TTS implementation (placeholder)."""
    
    def __init__(self):
        """Initialize Piper TTS."""
        self.model = None
        
        logger.debug("PiperTTS instantiated")
    
    async def initialize(self) -> None:
        """Initialize Piper model."""
        try:
            logger.debug("Initializing Piper TTS...")
            
            # TODO: Implement Piper TTS initialization
            # This is a placeholder for local TTS fallback
            
            logger.warning("Piper TTS not implemented yet, using placeholder")
            logger.info("Piper TTS initialized (placeholder)")
            
        except Exception as e:
            logger.error("Failed to initialize Piper", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech using Piper.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (WAV)
        """
        try:
            logger.debug("Synthesizing with Piper", extra={
                "text_length": len(text)
            })
            
            # TODO: Implement Piper synthesis
            # For now, return empty bytes
            
            logger.warning("Piper TTS not implemented, returning empty audio")
            
            return b""
            
        except Exception as e:
            logger.error("Piper synthesis failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close Piper model."""
        logger.debug("Closing Piper model...")
        self.model = None
        logger.info("Piper model closed")


# Factory function
def get_tts_service() -> TTSEngine:
    """
    Get the configured TTS service.
    
    Returns:
        TTS engine instance
    """
    provider = settings.tts_provider.lower()
    
    logger.debug(f"Creating TTS service: {provider}")
    
    if provider == "elevenlabs":
        service = ElevenLabsTTS()
    elif provider == "piper":
        service = PiperTTS()
    else:
        logger.error(f"Unknown TTS provider: {provider}")
        raise ValueError(f"Unknown TTS provider: {provider}")
    
    logger.info(f"TTS service created: {provider}")
    return service


# Global singleton
_tts_service: Optional[TTSEngine] = None


def get_global_tts() -> TTSEngine:
    """Get or create global TTS service instance."""
    global _tts_service
    
    if _tts_service is None:
        logger.debug("Creating global TTS service...")
        _tts_service = get_tts_service()
    
    return _tts_service


logger.debug("TTS service module loaded")
