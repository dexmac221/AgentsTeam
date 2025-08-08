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
    
    def __init__(self, config, logger: Logger, base_url: Optional[str] = None):
        """
        Initialize the Ollama client.
        
        Args:
            config: Configuration object containing Ollama settings
            logger (Logger): Logging utility for debugging and monitoring
            base_url (Optional[str]): Override the Ollama base URL for this client
        """
        self.config = config
        self.logger = logger
        self.base_url = base_url or config.get('ollama.base_url', 'http://localhost:11434')
    
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
            # Build messages with enhanced system prompt for code generation
            messages = []
            
            # Use enhanced system prompt for code generation
            if not system_prompt:
                system_prompt = self._get_default_system_prompt()
            
            # Enhance system prompt for better code generation
            enhanced_system_prompt = f"""{system_prompt}

CRITICAL INSTRUCTIONS:
- Generate ONLY executable code, no explanations or markdown
- Do NOT use ```code``` blocks or markdown formatting
- Do NOT include tables, descriptions, or explanatory text
- Start directly with code (imports, function definitions, etc.)
- Include comments INSIDE the code using proper comment syntax
- Make code complete and production-ready
- If generating multiple files, clearly separate them with file headers"""

            messages.append({"role": "system", "content": enhanced_system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for more consistent code
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": 4096  # Allow longer responses for complex code
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
                        content = result.get('message', {}).get('content', '')
                        
                        # Post-process to clean up common issues
                        return self._clean_generated_content(content)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
        
        except Exception as e:
            self.logger.error(f"Ollama generation error: {e}")
            raise Exception(f"Failed to generate with Ollama: {e}")
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for code generation"""
        return """You are an expert software developer specializing in clean, production-ready code generation. 
Generate only executable code without any explanatory text, markdown formatting, or documentation outside the code itself.
Follow best practices and include appropriate comments within the code."""
    
    def _clean_generated_content(self, content: str) -> str:
        """Clean common issues in generated content"""
        # Remove common prefixes that models sometimes add
        prefixes_to_remove = [
            "Here's the code:",
            "Here is the code:",
            "Below is the code:",
            "The code is:",
            "```python",
            "```javascript",
            "```html",
            "```css",
            "```json",
            "```",
        ]
        
        for prefix in prefixes_to_remove:
            if content.strip().startswith(prefix):
                content = content[len(prefix):].strip()
        
        # Remove trailing markdown
        if content.strip().endswith("```"):
            content = content.rsplit("```", 1)[0].strip()
        
        return content
    
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