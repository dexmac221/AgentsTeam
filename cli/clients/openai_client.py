"""
OpenAI Client - Professional client for OpenAI API interactions.

This module provides a robust interface for communicating with OpenAI's cloud
models, including GPT-4, GPT-3.5, and other models. It handles authentication,
rate limiting, error handling, and provides optimized text generation
capabilities for complex AI tasks.
"""

import aiohttp
import json
from typing import Dict, Optional
from ..utils.logger import Logger

class OpenAIClient:
    """
    Professional client for OpenAI API interactions.
    
    Provides secure and efficient communication with OpenAI's cloud models
    for high-quality text generation. Handles authentication, rate limiting,
    and error recovery for reliable AI interactions.
    
    Attributes:
        config: Configuration object with API keys and settings
        logger (Logger): Logging utility for debugging and monitoring
        api_key (str): OpenAI API key for authentication
        base_url (str): Base URL for OpenAI API endpoints
    """
    
    def __init__(self, config, logger: Logger):
        """
        Initialize the OpenAI client.
        
        Args:
            config: Configuration object containing OpenAI API key
            logger (Logger): Logging utility for debugging and monitoring
        """
        self.config = config
        self.logger = logger
        self.api_key = config.get('openai.api_key')
        self.base_url = "https://api.openai.com/v1"
    
    async def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using OpenAI cloud models.
        
        Args:
            model (str): OpenAI model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
            prompt (str): User prompt for text generation
            system_prompt (Optional[str]): Optional system prompt for context
            
        Returns:
            str: Generated text response from OpenAI
            
        Raises:
            Exception: If API key is missing or generation fails
        """
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages
            }
            
            # Configure parameters based on model type
            if model.startswith('gpt-4.1') or model.startswith('o4-'):
                # New models have restrictions - use defaults only
                payload["max_completion_tokens"] = 4000
            else:
                # Older models support more parameters
                payload["temperature"] = 0.1
                payload["top_p"] = 0.9
                payload["max_tokens"] = 4000
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 min timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        error_text = await response.text()
                        if response.status == 401:
                            raise Exception("Invalid OpenAI API key")
                        elif response.status == 429:
                            raise Exception("OpenAI API rate limit exceeded")
                        else:
                            raise Exception(f"OpenAI API error {response.status}: {error_text}")
        
        except Exception as e:
            self.logger.error(f"OpenAI generation error: {e}")
            if "API key" in str(e):
                raise
            raise Exception(f"Failed to generate with OpenAI: {e}")
    
    async def check_api_key(self) -> bool:
        """Check if API key is valid"""
        if not self.api_key:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except:
            return False