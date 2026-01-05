"""
Drop-in replacement for OpenAI client with babble injection.

Usage:
    # Instead of:
    from openai import OpenAI
    client = OpenAI()
    
    # Use:
    from bimbogpt import BimboClient
    client = BimboClient()
    
    # Works exactly the same:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Explain this in 1 word"}]
    )
"""

import os
from typing import Optional, Any
from dataclasses import dataclass

from .injector import BabbleInjector


@dataclass
class BimboConfig:
    """Configuration for babble injection."""
    enabled: bool = True
    babble_word: str = "blah"
    repetitions: Optional[int] = None
    auto_scale: bool = True
    verbose: bool = False


class _ChatCompletions:
    """Wrapper for chat.completions that injects babble."""
    
    def __init__(self, openai_client: Any, injector: BabbleInjector, config: BimboConfig):
        self._client = openai_client
        self._injector = injector
        self._config = config
    
    def create(self, messages: list[dict], **kwargs) -> Any:
        """
        Create a chat completion with automatic babble injection.
        
        If the messages contain a trigger phrase (e.g., "in 1 word"),
        babble priming is automatically injected.
        """
        if self._config.enabled:
            modified_messages, match = self._injector.inject(messages)
            
            if match and self._config.verbose:
                print(f"[BiMBoGPT] Detected trigger: '{match.original_phrase}' "
                      f"(mode={match.mode}, count={match.count})")
            
            messages = modified_messages
        
        return self._client.chat.completions.create(messages=messages, **kwargs)


class _Chat:
    """Wrapper for chat namespace."""
    
    def __init__(self, openai_client: Any, injector: BabbleInjector, config: BimboConfig):
        self.completions = _ChatCompletions(openai_client, injector, config)


class BimboClient:
    """
    Drop-in replacement for OpenAI client with babble injection.
    
    Automatically detects trigger phrases like "in 1 word" and injects
    babble priming to help models produce better reasoning chains.
    
    Example:
        from bimbogpt import BimboClient
        
        client = BimboClient()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "What's 2+2? Answer in 1 word."}]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        babble_word: str = "blah",
        repetitions: Optional[int] = None,
        auto_scale: bool = True,
        enabled: bool = True,
        verbose: bool = False,
        **openai_kwargs,
    ):
        """
        Initialize the BiMBo client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom API base URL (for compatible APIs)
            babble_word: Word to use for babble (default: "blah")
            repetitions: Fixed babble repetitions (None = auto-scale)
            auto_scale: Auto-adjust babble based on trigger mode
            enabled: Whether to inject babble (can disable for testing)
            verbose: Print when triggers are detected
            **openai_kwargs: Additional kwargs passed to OpenAI client
        """
        # Lazy import to avoid requiring openai at module load
        from openai import OpenAI
        
        self._config = BimboConfig(
            enabled=enabled,
            babble_word=babble_word,
            repetitions=repetitions,
            auto_scale=auto_scale,
            verbose=verbose,
        )
        
        self._injector = BabbleInjector(
            babble_word=babble_word,
            repetitions=repetitions,
            auto_scale=auto_scale,
        )
        
        # Create underlying OpenAI client
        client_kwargs = {**openai_kwargs}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self._openai = OpenAI(**client_kwargs)
        
        # Set up chat interface
        self.chat = _Chat(self._openai, self._injector, self._config)
    
    @property
    def openai(self) -> Any:
        """Access the underlying OpenAI client directly."""
        return self._openai
    
    def disable(self) -> None:
        """Disable babble injection."""
        self._config.enabled = False
    
    def enable(self) -> None:
        """Enable babble injection."""
        self._config.enabled = True
