"""
Model Selection Logic - Intelligent AI model selection and management.

This module provides sophisticated model selection capabilities for AgentsTeam,
automatically choosing between local Ollama models and cloud-based OpenAI models
based on task complexity, resource availability, and performance requirements.

The selector uses adaptive strategies to optimize for speed, quality, and cost:
- Simple tasks: Prefer fast local models for quick responses
- Medium tasks: Balance between local and cloud models
- Complex tasks: Use powerful cloud models for best quality

It also handles model availability checking, fallback strategies, and
performance monitoring to ensure optimal user experience.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from ..utils.logger import Logger

class ModelSelector:
    """
    Intelligent model selector for optimal AI model selection.
    
    This class handles the complex logic of choosing the best AI model for
    each task based on complexity, availability, and performance requirements.
    It manages both local Ollama models and cloud OpenAI models with
    sophisticated fallback strategies.
    
    The selector implements adaptive strategies:
    - Checks model availability in real-time
    - Balances speed vs quality based on task complexity
    - Provides graceful fallback when preferred models are unavailable
    - Monitors performance and adjusts recommendations
    
    Attributes:
        config: Configuration object with API keys and settings
        logger (Logger): Logging utility for debugging and monitoring
        ollama_base_url (str): Base URL for Ollama API
        openai_api_key (str): OpenAI API key for cloud models
    """
    
    def __init__(self, config, logger: Logger):
        """
        Initialize the model selector with configuration.
        
        Args:
            config: Configuration object containing API keys and URLs
            logger (Logger): Logging utility for debugging and monitoring
        """
        self.config = config
        self.logger = logger
        self.ollama_base_url = config.get('ollama.base_url', 'http://192.168.1.62:11434')
        self.openai_api_key = config.get('openai.api_key')
    
    async def select_model(self, complexity: str) -> Dict[str, str]:
        """
        Select the optimal model based on task complexity and availability.
        
        Uses intelligent selection logic to choose between local and cloud models
        based on the complexity of the task, resource availability, and
        performance requirements. Implements fallback strategies to ensure
        reliability.
        
        Args:
            complexity (str): Task complexity level ('simple', 'medium', 'complex')
            
        Returns:
            Dict[str, str]: Selected model information containing:
                - 'provider': Model provider ('ollama' or 'openai')
                - 'model': Specific model name
                - 'type': Model type classification
                - 'reasoning': Why this model was selected
                
        Example:
            >>> selector = ModelSelector(config, logger)
            >>> model = await selector.select_model('complex')
            >>> print(f"Selected {model['model']} from {model['provider']}")
        """
        
        # Model selection strategy - prioritize local Ollama models with gpt-oss
        if complexity == 'simple':
            # Always try local models first for simple tasks
            return await self._select_local_model() or await self._select_cloud_model('fast')
        
        elif complexity == 'medium':
            # Prefer larger local models, fallback to cloud only if needed
            return await self._select_local_model(prefer_large=True) or await self._select_cloud_model('balanced')
        
        else:  # complex
            # Still prefer local models (gpt-oss:20b is powerful enough), fallback to cloud
            return await self._select_local_model(prefer_large=True) or await self._select_cloud_model('powerful')
    
    async def _select_local_model(self, prefer_large: bool = False) -> Optional[Dict[str, str]]:
        """Select best available Ollama model"""
        try:
            models = await self.get_ollama_models()
            if not models:
                self.logger.debug("No Ollama models available")
                return None
            
            # Model preference order - prioritize gpt-oss:20b and coding models
            if prefer_large:
                preferred_order = [
                    'gpt-oss:20b', 'gpt-oss',  # New preferred high-quality model
                    'qwen2.5-coder:32b', 'qwen2.5-coder:14b', 'qwen2.5-coder:7b', 
                    'codellama:13b', 'codellama:7b', 'codellama',
                    'llama3.1:70b', 'llama3.1:8b', 'llama3:8b',
                    'gemma2:27b', 'gemma2:9b', 'gemma3n:latest',
                    'gemma2:2b'
                ]
            else:
                preferred_order = [
                    'gpt-oss:20b', 'gpt-oss',  # New preferred high-quality model
                    'qwen2.5-coder:7b', 'qwen2.5-coder:1.5b', 'qwen2.5-coder',
                    'codellama:7b', 'codellama',
                    'llama3.1:8b', 'llama3:8b', 'gemma2:9b',
                    'gemma3n:latest', 'gemma2:2b'
                ]
            
            # Find first available preferred model
            for preferred in preferred_order:
                for available in models:
                    if preferred.lower() in available.lower():
                        self.logger.info(f"Selected local model: {available}")
                        return {
                            'provider': 'ollama',
                            'model': available,
                            'base_url': self.ollama_base_url
                        }
            
            # Fallback to any available model
            model = models[0]
            self.logger.info(f"Selected fallback local model: {model}")
            return {
                'provider': 'ollama',
                'model': model,
                'base_url': self.ollama_base_url
            }
            
        except Exception as e:
            self.logger.error(f"Error selecting local model: {e}")
            return None
    
    async def _select_cloud_model(self, performance_tier: str) -> Dict[str, str]:
        """Select OpenAI model based on performance needs"""
        if not self.openai_api_key:
            raise Exception("OpenAI API key not configured. Run: agentsteam config --openai-key YOUR_KEY")
        
        # Select model based on performance tier - prioritizing new affordable models
        if performance_tier == 'fast':
            model = 'gpt-4.1-nano'  # Ultra-lightweight for simple tasks
        elif performance_tier == 'balanced':
            model = 'gpt-4.1-mini'  # Good balance of cost and quality
        else:  # powerful
            model = 'o4-mini'  # Reasoning-optimized for complex tasks
        
        self.logger.info(f"Selected cloud model: {model}")
        return {
            'provider': 'openai',
            'model': model,
            'api_key': self.openai_api_key
        }
    
    async def get_ollama_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        self.logger.debug(f"Found {len(models)} Ollama models")
                        return models
                    else:
                        self.logger.debug(f"Ollama API returned status: {response.status}")
                        return []
        except Exception as e:
            self.logger.debug(f"Could not connect to Ollama: {e}")
            return []
    
    def parse_model_string(self, model_str: str) -> Dict[str, str]:
        """Parse model string like 'ollama:gemma2' or 'openai:gpt-4'"""
        if ':' in model_str:
            provider, model = model_str.split(':', 1)
        else:
            # Try to guess provider
            if model_str.startswith('gpt-') or model_str.startswith('o4-') or 'gpt' in model_str.lower():
                provider, model = 'openai', model_str
            else:
                provider, model = 'ollama', model_str
        
        result = {'provider': provider, 'model': model}
        
        if provider == 'ollama':
            result['base_url'] = self.ollama_base_url
        elif provider == 'openai':
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            result['api_key'] = self.openai_api_key
        
        return result