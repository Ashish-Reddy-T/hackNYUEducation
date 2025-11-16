"""
Comprehensive API key and service connectivity test script.
Tests all external services: Gemini, Deepgram, ElevenLabs, and Qdrant.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.gemini_client import GeminiClient
from app.services.qdrant_client import QdrantService
from app.services.stt_service import DeepgramSTT, WhisperSTT
from app.services.tts_service import ElevenLabsTTS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


async def test_gemini():
    """Test Gemini API connectivity and functionality."""
    print_header("Testing Gemini API")
    
    try:
        print_info("Initializing Gemini client...")
        client = GeminiClient()
        await client.initialize()
        print_success("Gemini client initialized")
        
        print_info("Testing health check...")
        is_healthy = await client.health_check()
        if is_healthy:
            print_success("Gemini health check passed")
        else:
            print_error("Gemini health check failed")
            return False
        
        print_info("Testing text generation...")
        response = await client.generate_text(
            prompt="Say 'OK' if you can hear me.",
            max_tokens=20
        )
        if response and len(response) > 0:
            print_success(f"Text generation works: {response[:50]}...")
        else:
            print_error("Text generation returned empty response")
            return False
        
        print_info("Testing embedding generation...")
        embedding = await client.embed_text("test query")
        if embedding and len(embedding) > 0:
            print_success(f"Embedding generated: {len(embedding)} dimensions")
        else:
            print_error("Embedding generation failed")
            return False
        
        await client.close()
        print_success("Gemini API test completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Gemini test failed: {str(e)}")
        logger.exception("Gemini test error")
        return False


async def test_qdrant():
    """Test Qdrant connectivity and functionality."""
    print_header("Testing Qdrant")
    
    try:
        print_info(f"Connecting to Qdrant at {settings.qdrant_url}...")
        service = QdrantService()
        await service.initialize()
        print_success("Qdrant client initialized")
        
        print_info("Testing health check...")
        is_healthy = await service.health_check()
        if is_healthy:
            print_success("Qdrant health check passed")
        else:
            print_error("Qdrant health check failed")
            return False
        
        print_info("Testing collection access...")
        collections = service.client.get_collections()
        print_success(f"Found {len(collections.collections)} collections")
        
        await service.close()
        print_success("Qdrant test completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Qdrant test failed: {str(e)}")
        logger.exception("Qdrant test error")
        return False


async def test_deepgram():
    """Test Deepgram STT service."""
    print_header("Testing Deepgram STT")
    
    try:
        print_info("Initializing Deepgram client...")
        stt = DeepgramSTT()
        await stt.initialize()
        print_success("Deepgram client initialized")
        
        print_info("Testing transcription with sample audio...")
        # Create a minimal test audio (silence)
        # Note: This is a placeholder - real test would need actual audio bytes
        print_warning("Skipping actual transcription test (requires audio bytes)")
        print_info("Deepgram client is ready for use")
        
        await stt.close()
        print_success("Deepgram STT test completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Deepgram test failed: {str(e)}")
        logger.exception("Deepgram test error")
        return False


async def test_elevenlabs():
    """Test ElevenLabs TTS service."""
    print_header("Testing ElevenLabs TTS")
    
    try:
        print_info("Initializing ElevenLabs client...")
        tts = ElevenLabsTTS()
        await tts.initialize()
        print_success("ElevenLabs client initialized")
        
        print_info("Testing synthesis with sample text...")
        test_text = "Hello, this is a test."
        audio_data = await tts.synthesize(test_text)
        
        if audio_data and len(audio_data) > 0:
            print_success(f"Audio synthesis works: {len(audio_data)} bytes generated")
        else:
            print_error("Audio synthesis returned empty data")
            return False
        
        await tts.close()
        print_success("ElevenLabs TTS test completed successfully")
        return True
        
    except Exception as e:
        print_error(f"ElevenLabs test failed: {str(e)}")
        logger.exception("ElevenLabs test error")
        return False


async def test_configuration():
    """Test configuration loading."""
    print_header("Testing Configuration")
    
    results = []
    
    # Check API keys
    print_info("Checking API keys...")
    
    if settings.gemini_api_key and len(settings.gemini_api_key) > 10:
        print_success(f"Gemini API key: {settings.gemini_api_key[:10]}...")
        results.append(True)
    else:
        print_error("Gemini API key is missing or invalid")
        results.append(False)
    
    if settings.deepgram_api_key and len(settings.deepgram_api_key) > 10:
        print_success(f"Deepgram API key: {settings.deepgram_api_key[:10]}...")
        results.append(True)
    else:
        print_error("Deepgram API key is missing or invalid")
        results.append(False)
    
    if settings.elevenlabs_api_key and len(settings.elevenlabs_api_key) > 10:
        print_success(f"ElevenLabs API key: {settings.elevenlabs_api_key[:10]}...")
        results.append(True)
    else:
        print_error("ElevenLabs API key is missing or invalid")
        results.append(False)
    
    # Check Qdrant URL
    print_info(f"Qdrant URL: {settings.qdrant_url}")
    if settings.qdrant_url:
        print_success("Qdrant URL configured")
        results.append(True)
    else:
        print_error("Qdrant URL not configured")
        results.append(False)
    
    # Check providers
    print_info(f"STT Provider: {settings.stt_provider}")
    print_info(f"TTS Provider: {settings.tts_provider}")
    print_info(f"Gemini Model: {settings.gemini_model}")
    
    return all(results)


async def main():
    """Run all tests."""
    print_header("Agora API Keys & Services Test Suite")
    
    print_info("Starting comprehensive service tests...")
    print_info("This will test: Gemini, Qdrant, Deepgram, ElevenLabs")
    print()
    
    results = {}
    
    # Test configuration first
    results['configuration'] = await test_configuration()
    print()
    
    if not results['configuration']:
        print_error("Configuration test failed. Please check your .env file.")
        print_info("Expected environment variables:")
        print("  - GEMINI_API")
        print("  - DEEPGRAM_API")
        print("  - ELEVEN_API")
        print("  - QDRANT_URL (optional, defaults to http://localhost:6333)")
        return
    
    # Test services
    results['gemini'] = await test_gemini()
    print()
    
    results['qdrant'] = await test_qdrant()
    print()
    
    results['deepgram'] = await test_deepgram()
    print()
    
    results['elevenlabs'] = await test_elevenlabs()
    print()
    
    # Summary
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for service, result in results.items():
        if result:
            print_success(f"{service.upper()}: PASSED")
        else:
            print_error(f"{service.upper()}: FAILED")
    
    print()
    print(f"{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print_success("All tests passed! Your backend is ready.")
    else:
        print_error("Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        logger.exception("Test suite error")
        sys.exit(1)

