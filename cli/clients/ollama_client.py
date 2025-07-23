"""
Ollama Client - High-performance client for local Ollama API interactions.

This module provides a streamlined interface for communicating with local
Ollama models, offering text generation, model management, and health checking
capabilities. It's optimized for low-latency interactions with local models
while providing robust error handling and connection management.
"""

import aiohttp
import json
from typing import Dict, Optional
from ..utils.logger import Logger

class OllamaClient:
    """
    High-performance client for local Ollama API interactions.
    
    Provides efficient communication with local Ollama models for text generation,
    model management, and health monitoring. Optimized for low-latency local
    model interactions with robust error handling.
    
    Attributes:
        config: Configuration object with Ollama settings
        logger (Logger): Logging utility for debugging and monitoring
        base_url (str): Base URL for Ollama API endpoint
    """
    
    def __init__(self, config, logger: Logger):
        """
        Initialize the Ollama client.
        
        Args:
            config: Configuration object containing Ollama settings
            logger (Logger): Logging utility for debugging and monitoring
        """
        self.config = config
        self.logger = logger
        self.base_url = config.get('ollama.base_url', 'http://localhost:11434')
    
    async def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using a local Ollama model.
        
        Args:
            model (str): Name of the Ollama model to use
            prompt (str): User prompt for text generation
            system_prompt (Optional[str]): Optional system prompt for context
            
        Returns:
            str: Generated text response from the model
            
        Raises:
            Exception: If model is unavailable or generation fails
        """
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for more consistent code
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 min timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('message', {}).get('content', '')
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
        
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            raise Exception(f"Failed to generate with Ollama: {e}")
    
    async def check_model_available(self, model: str) -> bool:
        """Check if a model is available locally"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        available_models = [m['name'] for m in data.get('models', [])]
                        return any(model in available for available in available_models)
        except:
            pass
        return False