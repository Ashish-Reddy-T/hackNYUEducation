"""
Speech-to-Text (STT) service with pluggable providers.
Supports Deepgram API and local Whisper.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class STTEngine(ABC):
    """Abstract base class for STT engines."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the STT engine."""
        pass
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes, format: str = "webm") -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (webm, wav, mp3, etc.)
        
        Returns:
            Transcribed text
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup resources."""
        pass


class DeepgramSTT(STTEngine):
    """Deepgram API STT implementation."""
    
    def __init__(self):
        """Initialize Deepgram STT."""
        self.api_key = settings.deepgram_api_key
        self.client = None
        
        logger.debug("DeepgramSTT instantiated", extra={
            "api_key_length": len(self.api_key)
        })
    
    async def initialize(self) -> None:
        """Initialize Deepgram client."""
        try:
            logger.debug("Initializing Deepgram client...")
            
            from deepgram import DeepgramClient
            
            self.client = DeepgramClient(api_key=self.api_key)
            
            logger.info("Deepgram STT initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Deepgram", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def transcribe(self, audio_data: bytes, format: str = "webm") -> str:
        """
        Transcribe audio using Deepgram.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format
        
        Returns:
            Transcribed text
        """
        try:
            logger.debug("Transcribing with Deepgram", extra={
                "audio_size": len(audio_data),
                "format": format
            })
            
            if not self.client:
                raise RuntimeError("Deepgram client not initialized")
            
            # Prepare options
            from deepgram import PrerecordedOptions
            
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                punctuate=True,
                language="en"
            )
            
            logger.debug("Calling Deepgram API...", extra={
                "model": "nova-2",
                "options": str(options)
            })
            
            # Transcribe
            response = self.client.listen.rest.v("1").transcribe_file(
                {"buffer": audio_data},
                options
            )
            
            # Extract transcript
            transcript = ""
            if response.results and response.results.channels:
                channel = response.results.channels[0]
                if channel.alternatives:
                    transcript = channel.alternatives[0].transcript
            
            logger.info("Deepgram transcription completed", extra={
                "audio_size": len(audio_data),
                "transcript_length": len(transcript),
                "confidence": channel.alternatives[0].confidence if channel.alternatives else None
            })
            
            return transcript
            
        except Exception as e:
            logger.error("Deepgram transcription failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "audio_size": len(audio_data)
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close Deepgram client."""
        logger.debug("Closing Deepgram client...")
        self.client = None
        logger.info("Deepgram client closed")


class WhisperSTT(STTEngine):
    """Local Whisper STT implementation using faster-whisper."""
    
    def __init__(self):
        """Initialize Whisper STT."""
        self.model_name = settings.whisper_model
        self.model = None
        
        logger.debug("WhisperSTT instantiated", extra={
            "model": self.model_name
        })
    
    async def initialize(self) -> None:
        """Initialize Whisper model."""
        try:
            logger.debug(f"Loading Whisper model: {self.model_name}...")
            
            from faster_whisper import WhisperModel
            
            self.model = WhisperModel(
                self.model_name,
                device="cpu",  # Use "cuda" if GPU available
                compute_type="int8"
            )
            
            logger.info("Whisper STT initialized successfully", extra={
                "model": self.model_name,
                "device": "cpu"
            })
            
        except Exception as e:
            logger.error("Failed to initialize Whisper", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "model": self.model_name
            }, exc_info=True)
            raise
    
    async def transcribe(self, audio_data: bytes, format: str = "webm") -> str:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format
        
        Returns:
            Transcribed text
        """
        try:
            logger.debug("Transcribing with Whisper", extra={
                "audio_size": len(audio_data),
                "format": format,
                "model": self.model_name
            })
            
            if not self.model:
                raise RuntimeError("Whisper model not initialized")
            
            # Save audio to temporary file (Whisper requires file path)
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_data)
            
            logger.debug(f"Audio saved to temp file: {temp_path}")
            
            try:
                # Transcribe
                logger.debug("Running Whisper transcription...")
                segments, info = self.model.transcribe(
                    temp_path,
                    language="en",
                    beam_size=5
                )
                
                # Combine segments
                transcript = " ".join([segment.text for segment in segments])
                
                logger.info("Whisper transcription completed", extra={
                    "audio_size": len(audio_data),
                    "transcript_length": len(transcript),
                    "language": info.language,
                    "language_probability": info.language_probability
                })
                
                return transcript.strip()
                
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    logger.debug(f"Temp file deleted: {temp_path}")
            
        except Exception as e:
            logger.error("Whisper transcription failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "audio_size": len(audio_data)
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close Whisper model."""
        logger.debug("Closing Whisper model...")
        self.model = None
        logger.info("Whisper model closed")


# Factory function
def get_stt_service() -> STTEngine:
    """
    Get the configured STT service.
    
    Returns:
        STT engine instance
    """
    provider = settings.stt_provider.lower()
    
    logger.debug(f"Creating STT service: {provider}")
    
    if provider == "deepgram":
        service = DeepgramSTT()
    elif provider == "whisper":
        service = WhisperSTT()
    else:
        logger.error(f"Unknown STT provider: {provider}")
        raise ValueError(f"Unknown STT provider: {provider}")
    
    logger.info(f"STT service created: {provider}")
    return service


# Global singleton
_stt_service: Optional[STTEngine] = None
_stt_initialized: bool = False


async def get_global_stt() -> STTEngine:
    """Get or create global STT service instance."""
    global _stt_service, _stt_initialized
    
    if _stt_service is None:
        logger.debug("Creating global STT service...")
        _stt_service = get_stt_service()
    
    if not _stt_initialized:
        logger.debug("Initializing global STT service...")
        await _stt_service.initialize()
        _stt_initialized = True
    
    return _stt_service


logger.debug("STT service module loaded")
