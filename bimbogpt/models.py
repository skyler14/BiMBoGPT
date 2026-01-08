"""
Multi-model provider support via JSONL config.

Loads model configurations from models.jsonl, allowing users to configure
multiple LLM providers (OpenAI, Groq, Anthropic, Ollama, etc).

Config format (one JSON object per line):
{"name": "groq-llama3", "provider": "groq", "model": "llama-3.3-70b-versatile", "api_key": "...", "base_url": "..."}
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for a model provider."""
    name: str
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    def get_client(self):
        """
        Get an OpenAI-compatible client for this model.
        
        Uses the openai library for OpenAI-compatible APIs (OpenAI, Groq, Ollama).
        """
        from openai import OpenAI
        
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
            
        return OpenAI(**kwargs)


def find_models_file() -> Optional[Path]:
    """Find models.jsonl in current dir or home config."""
    paths = [
        Path.cwd() / "models.jsonl",
        Path.home() / ".bimbogpt" / "models.jsonl",
    ]
    
    for path in paths:
        if path.exists():
            return path
    
    return None


def load_models(path: Optional[Path] = None) -> dict[str, ModelConfig]:
    """
    Load model configs from JSONL file.
    
    Returns dict mapping model name to ModelConfig.
    Logs warnings for invalid or duplicate entries.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if path is None:
        path = find_models_file()
    
    if path is None or not path.exists():
        return {}
    
    models = {}
    seen_names = set()
    
    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"models.jsonl line {line_num}: invalid JSON - {e}")
                continue
            
            # Validate required fields
            if 'name' not in data:
                logger.warning(f"models.jsonl line {line_num}: missing required 'name' field")
                continue
            if 'model' not in data:
                logger.warning(f"models.jsonl line {line_num}: missing required 'model' field")
                continue
            
            name = data['name']
            
            # Detect duplicates
            if name in seen_names:
                logger.warning(f"models.jsonl line {line_num}: duplicate name '{name}', overwriting previous")
            seen_names.add(name)
            
            config = ModelConfig(
                name=name,
                provider=data.get("provider", "openai"),
                model=data["model"],
                api_key=data.get("api_key"),
                base_url=data.get("base_url"),
            )
            models[name] = config
    
    return models


def get_model(name: str) -> Optional[ModelConfig]:
    """Get a specific model config by name."""
    models = load_models()
    return models.get(name)


def list_models() -> list[str]:
    """List available model names."""
    return list(load_models().keys())


def query_model(
    name: str,
    messages: list[dict],
    max_retries: int = 3,
    **kwargs
) -> str:
    """
    Query a configured model with babble support and automatic retry.
    
    Args:
        name: Model name from models.jsonl
        messages: OpenAI-style messages
        max_retries: Maximum retry attempts for transient errors (default: 3)
        **kwargs: Additional args for chat.completions.create
        
    Returns:
        Response content string
        
    Raises:
        ValueError: If model not found
        Exception: If all retries fail
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    
    config = get_model(name)
    if config is None:
        raise ValueError(f"Model '{name}' not found in models.jsonl")
    
    from .client import BimboClient
    
    # Create BimboClient with this model's settings
    client_kwargs = {}
    if config.api_key:
        client_kwargs["api_key"] = config.api_key
    if config.base_url:
        client_kwargs["base_url"] = config.base_url
    
    client = BimboClient(**client_kwargs)
    
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_name = type(e).__name__
            
            # Check if it's a retryable error (rate limit, server error)
            is_retryable = (
                "RateLimitError" in error_name or
                "429" in str(e) or
                "503" in str(e) or
                "APIError" in error_name
            )
            
            if is_retryable and attempt < max_retries - 1:
                wait_time = (2 ** attempt)  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise
    
    raise last_error
