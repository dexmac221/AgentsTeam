"""
OpenAI Client - Professional client for OpenAI API interactions.

This module provides a robust interface for communicating with OpenAI's cloud
models, including GPT-4 and GPT-4o family. It handles authentication,
rate limiting, error handling, and provides optimized text generation
capabilities for complex AI tasks.
"""

import aiohttp
import json
from typing import Dict, Optional, AsyncGenerator
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
    
    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        *,
        code_only: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: int = 4000,
    ) -> str:
        """
        Generate text using OpenAI cloud models.
        
        Args:
            model (str): OpenAI model name (e.g., 'gpt-4.1-mini', 'gpt-4o-mini')
            prompt (str): User prompt for text generation
            system_prompt (Optional[str]): Optional system prompt for context
            code_only (bool): If True, enforce code-only output (no prose/markdown)
            temperature (Optional[float]): Sampling temperature override
            top_p (Optional[float]): Nucleus sampling override
            max_tokens (int): Max tokens to generate
            
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
            final_system_prompt = system_prompt or "You are a helpful coding assistant."

            # Optionally enforce code-only behavior
            if code_only:
                final_system_prompt = (
                    "You are a code generation AI. Output ONLY executable code and code comments. "
                    "Do NOT use markdown backticks. Do NOT include explanations, intros, or outros."
                )
            messages.append({"role": "system", "content": final_system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                # Conservative defaults that work across chat/completions models
                "temperature": 0.1 if temperature is None else float(temperature),
                "top_p": 0.9 if top_p is None else float(top_p),
                "max_tokens": int(max_tokens),
                "stream": False,
            }
            
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

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        *,
        code_only: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from OpenAI chat completions (server-sent events).

        Yields incremental content strings as they arrive.
        """
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        messages = []
        final_system_prompt = system_prompt or "You are a helpful coding assistant."
        if code_only:
            final_system_prompt = (
                "You are a code generation AI. Output ONLY executable code and code comments. "
                "Do NOT use markdown backticks. Do NOT include explanations, intros, or outros."
            )
        messages.append({"role": "system", "content": final_system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1 if temperature is None else float(temperature),
            "top_p": 0.9 if top_p is None else float(top_p),
            "max_tokens": int(max_tokens),
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"OpenAI API error {resp.status}: {error_text}")

                buffer = ""
                async for chunk in resp.content.iter_any():
                    try:
                        buffer += chunk.decode('utf-8')
                    except Exception:
                        continue

                    # Split on double newline boundaries typical for SSE
                    while "\n\n" in buffer:
                        part, buffer = buffer.split("\n\n", 1)
                        line = part.strip()
                        if not line:
                            continue
                        # Each event may contain multiple lines; process lines beginning with data:
                        for ev_line in line.splitlines():
                            ev_line = ev_line.strip()
                            if not ev_line.startswith("data:"):
                                continue
                            data = ev_line[len("data:"):].strip()
                            if data == "[DONE]":
                                return
                            try:
                                obj = json.loads(data)
                                delta = obj['choices'][0]['delta'].get('content')
                                if delta:
                                    yield delta
                            except Exception:
                                # Ignore parse errors on keep-alive chunks
                                continue
    
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