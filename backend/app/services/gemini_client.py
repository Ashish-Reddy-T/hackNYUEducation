"""
Gemini API client for text generation, multimodal understanding, and embeddings.
Handles all interactions with Google's Gemini 2.5 Pro API.
"""
import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse, HarmBlockThreshold, HarmCategory

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        self.model_name = settings.gemini_model
        self.temperature = settings.gemini_temperature
        self.max_tokens = settings.gemini_max_tokens
        self.model: Optional[genai.GenerativeModel] = None
        self.embedding_model: Optional[Any] = None
        
        logger.debug("GeminiClient instantiated", extra={
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        })
    
    async def initialize(self) -> None:
        """Initialize the Gemini API client."""
        try:
            logger.debug("Configuring Gemini API...")
            genai.configure(api_key=settings.gemini_api_key)
            
            logger.debug(f"Creating GenerativeModel: {self.model_name}")
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            logger.debug("Creating embedding model: text-embedding-004")
            self.embedding_model = genai.GenerativeModel("text-embedding-004")
            
            logger.info("Gemini client initialized successfully", extra={
                "model": self.model_name,
                "embedding_model": "text-embedding-004"
            })
            
        except Exception as e:
            logger.error("Failed to initialize Gemini client", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close the Gemini client and cleanup resources."""
        logger.debug("Closing Gemini client...")
        self.model = None
        self.embedding_model = None
        logger.info("Gemini client closed")
    
    async def health_check(self) -> bool:
        """
        Check if Gemini API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            logger.debug("Performing Gemini health check...")
            
            if not self.model:
                logger.warning("Gemini model not initialized")
                return False
            
            # Simple test generation
            response = await self.generate_text(
                prompt="Say 'OK' if you can hear me.",
                max_tokens=10
            )
            
            is_healthy = response and len(response) > 0
            logger.debug("Gemini health check completed", extra={
                "healthy": is_healthy,
                "response_length": len(response) if response else 0
            })
            
            return is_healthy
            
        except Exception as e:
            logger.error("Gemini health check failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            return False
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Override default temperature
            max_tokens: Override default max tokens
        
        Returns:
            Generated text response
        """
        try:
            logger.debug("Generating text with Gemini", extra={
                "prompt_length": len(prompt),
                "has_system_prompt": system_prompt is not None,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            })
            
            if not self.model:
                logger.error("Gemini model not initialized")
                raise RuntimeError("Gemini model not initialized. Call initialize() first.")
            
            # Build full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                logger.debug("System prompt included", extra={
                    "system_prompt_length": len(system_prompt)
                })
            
            # Generate
            logger.debug("Calling Gemini API...")
            response: GenerateContentResponse = self.model.generate_content(full_prompt)
            
            generated_text = response.text
            
            logger.info("Text generated successfully", extra={
                "input_length": len(full_prompt),
                "output_length": len(generated_text),
                "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else "unknown"
            })
            
            return generated_text
            
        except Exception as e:
            logger.error("Text generation failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "prompt_length": len(prompt)
            }, exc_info=True)
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON-structured output using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            schema: Optional JSON schema for validation
        
        Returns:
            Parsed JSON dictionary
        """
        try:
            logger.debug("Generating JSON with Gemini", extra={
                "prompt_length": len(prompt),
                "has_schema": schema is not None
            })
            
            # Add JSON instruction to system prompt
            json_instruction = "\nYou must respond with valid JSON only. No other text."
            enhanced_system = (system_prompt or "") + json_instruction
            
            response_text = await self.generate_text(
                prompt=prompt,
                system_prompt=enhanced_system
            )
            
            logger.debug("Parsing JSON response...")
            
            # Extract JSON from response (handle markdown code blocks)
            import json
            import re
            
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("Extracted JSON from markdown code block")
            else:
                json_str = response_text.strip()
                logger.debug("Using raw response as JSON")
            
            parsed_json = json.loads(json_str)
            
            logger.info("JSON generated and parsed successfully", extra={
                "keys": list(parsed_json.keys()),
                "response_length": len(response_text)
            })
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", extra={
                "error": str(e),
                "response": response_text[:500]
            }, exc_info=True)
            raise
        except Exception as e:
            logger.error("JSON generation failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        mime_type: str = "image/jpeg"
    ) -> str:
        """
        Analyze an image using Gemini's multimodal capabilities.
        
        Args:
            image_data: Raw image bytes
            prompt: Analysis prompt
            mime_type: Image MIME type
        
        Returns:
            Analysis text
        """
        try:
            logger.debug("Analyzing image with Gemini", extra={
                "image_size": len(image_data),
                "mime_type": mime_type,
                "prompt_length": len(prompt)
            })
            
            if not self.model:
                logger.error("Gemini model not initialized")
                raise RuntimeError("Gemini model not initialized")
            
            # Create image part
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            logger.debug("Image loaded", extra={
                "format": image.format,
                "size": image.size,
                "mode": image.mode
            })
            
            # Generate content with image
            logger.debug("Calling Gemini API with image...")
            response = self.model.generate_content([prompt, image])
            
            analysis = response.text
            
            logger.info("Image analyzed successfully", extra={
                "analysis_length": len(analysis),
                "image_size": len(image_data)
            })
            
            return analysis
            
        except Exception as e:
            logger.error("Image analysis failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "image_size": len(image_data)
            }, exc_info=True)
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            logger.debug("Generating embedding", extra={
                "text_length": len(text)
            })
            
            if not self.embedding_model:
                logger.error("Embedding model not initialized")
                raise RuntimeError("Embedding model not initialized")
            
            # Generate embedding
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            
            logger.debug("Embedding generated", extra={
                "text_length": len(text),
                "embedding_dim": len(embedding)
            })
            
            return embedding
            
        except Exception as e:
            logger.error("Embedding generation failed", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(text)
            }, exc_info=True)
            raise
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding vector for search query.
        
        Args:
            query: Search query text
        
        Returns:
            Query embedding vector
        """
        try:
            logger.debug("Generating query embedding", extra={
                "query_length": len(query)
            })
            
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            
            embedding = result['embedding']
            
            logger.debug("Query embedding generated", extra={
                "query_length": len(query),
                "embedding_dim": len(embedding)
            })
            
            return embedding
            
        except Exception as e:
            logger.error("Query embedding failed", extra={
                "error": str(e),
                "error_type": type(e).__name__
            }, exc_info=True)
            raise


# Global singleton instance
gemini_service = GeminiClient()

logger.debug("Gemini service singleton created")
