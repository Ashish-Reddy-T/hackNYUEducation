"""
Text-to-Speech (TTS) service with pluggable providers.
Supports ElevenLabs API and local Piper.
"""
import io
import tempfile
import os

import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment
except ImportError:
    logger.warning("pydub not installed. PiperTTS will output WAV.")
    AudioSegment = None

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
            
            # Verify model is set correctly
            if not self.model or self.model == "eleven_monolingual_v1" or self.model == "eleven_multilingual_v1":
                logger.warning(f"Model '{self.model}' may be deprecated. Consider using 'eleven_turbo_v2' for free tier.")
            
            logger.info("ElevenLabs TTS initialized successfully", extra={
                "voice_id": self.voice_id,
                "model": self.model,
                "api_key_length": len(self.api_key) if self.api_key else 0
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
                "voice_id": self.voice_id,
                "model": self.model
            })
            
            if not self.client:
                raise RuntimeError("ElevenLabs client not initialized")
            
            logger.debug("Calling ElevenLabs API...", extra={
                "model": self.model,
                "voice_id": self.voice_id
            })
            
            # Generate audio using the new API format
            # The convert method returns a generator that yields audio chunks
            # Note: model_id parameter name may vary by SDK version
            try:
                # Try with model_id parameter (newer SDK versions)
                audio_stream = self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text,
                    model_id=self.model
                )
            except TypeError:
                # Fallback: try with model parameter (older SDK versions)
                logger.debug("Trying with 'model' parameter instead of 'model_id'")
                audio_stream = self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text,
                    model=self.model
                )
            
            # Collect audio chunks from the stream
            audio_chunks = []
            for chunk in audio_stream:
                if chunk:
                    audio_chunks.append(chunk)
            
            audio_data = b"".join(audio_chunks)
            
            if not audio_data or len(audio_data) == 0:
                logger.warning("ElevenLabs returned empty audio data")
                raise RuntimeError("Empty audio data received from ElevenLabs")
            
            logger.info("ElevenLabs synthesis completed", extra={
                "text_length": len(text),
                "audio_size": len(audio_data),
                "model": self.model
            })
            
            return audio_data
            
        except Exception as e:
            logger.error("ElevenLabs synthesis failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(text),
                "model": self.model,
                "voice_id": self.voice_id
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close ElevenLabs client."""
        logger.debug("Closing ElevenLabs client...")
        self.client = None
        logger.info("ElevenLabs client closed")


class PiperTTS(TTSEngine):
    """Local Piper TTS implementation using pyttsx3."""
    
    def __init__(self):
        """Initialize Piper TTS."""
        self.engine = None
        
        logger.debug("PiperTTS instantiated")
    
    async def initialize(self) -> None:
        """Initialize Piper/pyttsx3 engine."""
        try:
            logger.debug("Initializing Piper TTS (pyttsx3)...")
            
            import pyttsx3
            
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', 175)  # Speed
            self.engine.setProperty('volume', 1.0)  # Volume
            
            # Try to set a better voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer a female voice for tutor
                for voice in voices:
                    if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        logger.debug(f"Using voice: {voice.name}")
                        break
            
            logger.info("Piper TTS (pyttsx3) initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Piper", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech using pyttsx3 and convert to MP3.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (MP3)
        """
        try:
            logger.debug("Synthesizing with Piper (pyttsx3)", extra={
                "text_length": len(text)
            })
            
            if not self.engine:
                raise RuntimeError("Piper engine not initialized")
            
            if AudioSegment is None:
                raise RuntimeError("pydub is not installed. Cannot convert to MP3.")

            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            logger.debug(f"Saving temporary WAV to: {temp_path}")
            
            try:
                # Generate speech to file
                self.engine.save_to_file(text, temp_path)
                self.engine.runAndWait()
                
                # Read the audio file
                with open(temp_path, 'rb') as f:
                    wav_data = f.read()
                
                if not wav_data:
                    logger.error("pyttsx3 generated an empty WAV file")
                    raise RuntimeError("pyttsx3 generated empty audio")

                # --- NEW CONVERSION BLOCK ---
                logger.debug("Converting WAV to MP3...", extra={
                    "wav_size": len(wav_data)
                })
                wav_stream = io.BytesIO(wav_data)
                audio_segment = AudioSegment.from_wav(wav_stream)
                
                mp3_stream = io.BytesIO()
                audio_segment.export(mp3_stream, format="mp3")
                mp3_data = mp3_stream.getvalue()
                # --- END CONVERSION BLOCK ---

                logger.info("Piper synthesis completed and converted to MP3", extra={
                    "text_length": len(text),
                    "wav_size": len(wav_data),
                    "mp3_size": len(mp3_data)
                })
                
                return mp3_data
                
            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    logger.debug(f"Temp file deleted: {temp_path}")
            
        except Exception as e:
            logger.error("Piper synthesis failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close Piper engine."""
        logger.debug("Closing Piper engine...")
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        self.engine = None
        logger.info("Piper engine closed")


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
_tts_initialized: bool = False


async def get_global_tts() -> TTSEngine:
    """Get or create global TTS service instance."""
    global _tts_service, _tts_initialized
    
    if _tts_service is None:
        logger.debug("Creating global TTS service...")
        _tts_service = get_tts_service()
    
    if not _tts_initialized:
        logger.debug("Initializing global TTS service...")
        await _tts_service.initialize()
        _tts_initialized = True
    
    return _tts_service


logger.debug("TTS service module loaded")
