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
    """
    if path is None:
        path = find_models_file()
    
    if path is None or not path.exists():
        return {}
    
    models = {}
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                data = json.loads(line)
                config = ModelConfig(
                    name=data["name"],
                    provider=data.get("provider", "openai"),
                    model=data["model"],
                    api_key=data.get("api_key"),
                    base_url=data.get("base_url"),
                )
                models[config.name] = config
            except (json.JSONDecodeError, KeyError):
                continue
    
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
    **kwargs
) -> str:
    """
    Query a configured model with babble support.
    
    Args:
        name: Model name from models.jsonl
        messages: OpenAI-style messages
        **kwargs: Additional args for chat.completions.create
        
    Returns:
        Response content string
    """
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
    
    response = client.chat.completions.create(
        model=config.model,
        messages=messages,
        **kwargs
    )
    
    return response.choices[0].message.content
