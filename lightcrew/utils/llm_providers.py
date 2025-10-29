"""
LLM provider implementations for LightCrew framework.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from ..core.base import LLMProvider
from .logger import get_logger


logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name
            api_key: OpenAI API key
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None
    
    def _setup(self):
        """Setup OpenAI client."""
        try:
            import openai
            
            # Get API key from config or environment
            api_key = self.api_key or self.config.get("api_key")
            if not api_key:
                import os
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            self._client = openai.AsyncOpenAI(api_key=api_key)
            logger.info(f"OpenAI provider initialized with model: {self.model}")
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        if not self._initialized:
            self.initialize()
        
        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous generation method."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.generate(prompt, **kwargs))


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229", api_key: Optional[str] = None, **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            model: Anthropic model name
            api_key: Anthropic API key
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self._client = None
    
    def _setup(self):
        """Setup Anthropic client."""
        try:
            import anthropic
            
            # Get API key from config or environment
            api_key = self.api_key or self.config.get("api_key")
            if not api_key:
                import os
                api_key = os.getenv("ANTHROPIC_API_KEY")
            
            if not api_key:
                raise ValueError("Anthropic API key not provided")
            
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
            logger.info(f"Anthropic provider initialized with model: {self.model}")
            
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API."""
        if not self._initialized:
            self.initialize()
        
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
    
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous generation method."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.generate(prompt, **kwargs))


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, model: str = "mock-model", **kwargs):
        """
        Initialize mock provider.
        
        Args:
            model: Mock model name
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.response_template = kwargs.get("response_template", "Mock response to: {prompt}")
    
    def _setup(self):
        """Setup mock provider."""
        logger.info(f"Mock LLM provider initialized with model: {self.model}")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock response
        response = self.response_template.format(prompt=prompt[:100])
        
        # Add some randomness for testing
        import random
        if random.random() < 0.1:  # 10% chance of "failure"
            raise Exception("Mock LLM failure for testing")
        
        return response
    
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous generation method."""
        import time
        time.sleep(0.1)  # Simulate delay
        
        response = self.response_template.format(prompt=prompt[:100])
        
        # Add some randomness for testing
        import random
        if random.random() < 0.1:  # 10% chance of "failure"
            raise Exception("Mock LLM failure for testing")
        
        return response


class LocalLLMProvider(LLMProvider):
    """Local LLM provider using transformers or similar."""
    
    def __init__(self, model: str, model_path: Optional[str] = None, **kwargs):
        """
        Initialize local LLM provider.
        
        Args:
            model: Model name or path
            model_path: Path to local model files
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.model_path = model_path or model
        self._pipeline = None
    
    def _setup(self):
        """Setup local model."""
        try:
            from transformers import pipeline
            
            self._pipeline = pipeline(
                "text-generation",
                model=self.model_path,
                device_map="auto" if self.config.get("use_gpu", False) else "cpu",
                **self.config
            )
            
            logger.info(f"Local LLM provider initialized with model: {self.model}")
            
        except ImportError:
            raise ImportError("Transformers package not installed. Install with: pip install transformers")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using local model."""
        if not self._initialized:
            self.initialize()
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _generate():
                result = self._pipeline(
                    prompt,
                    max_length=kwargs.get("max_tokens", 1000),
                    temperature=kwargs.get("temperature", 0.7),
                    do_sample=True,
                    num_return_sequences=1
                )
                return result[0]["generated_text"][len(prompt):].strip()
            
            response = await loop.run_in_executor(None, _generate)
            return response
            
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise
    
    def generate_sync(self, prompt: str, **kwargs) -> str:
        """Synchronous generation method."""
        if not self._initialized:
            self.initialize()
        
        try:
            result = self._pipeline(
                prompt,
                max_length=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                do_sample=True,
                num_return_sequences=1
            )
            return result[0]["generated_text"][len(prompt):].strip()
            
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise


# Provider factory
def create_llm_provider(provider: str, model: str, **kwargs) -> LLMProvider:
    """
    Create an LLM provider instance.
    
    Args:
        provider: Provider name (openai, anthropic, local, mock)
        model: Model name
        **kwargs: Additional configuration
        
    Returns:
        LLM provider instance
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": LocalLLMProvider,
        "mock": MockLLMProvider
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown LLM provider: {provider}")
    
    return providers[provider](model=model, **kwargs)