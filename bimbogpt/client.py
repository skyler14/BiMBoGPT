"""
Drop-in replacement for OpenAI client with babble injection.

DESIGN: Minimal interception, maximum forward compatibility.
- Inherits from OpenAI
- Only intercepts chat.completions.create()
- All other methods/attributes pass through unchanged
- Uses __getattr__ for full compatibility with future SDK changes
"""

import logging
from typing import Optional, Any, Union
from openai import OpenAI

from .injector import BabbleInjector
from .stripper import strip_babble

log: logging.Logger = logging.getLogger(__name__)


class BimboClient(OpenAI):
    """
    OpenAI client with automatic babble injection.
    
    Inherits from OpenAI - just change your import.
    Only intercepts chat.completions.create(), everything else
    passes through unchanged for maximum forward compatibility.
    
    Example:
        from bimbogpt import BimboClient as OpenAI
        
        client = OpenAI()
        response = client.chat.completions.create(...)
    """
    
    def __init__(
        self,
        *args,
        babble_word: str = "blah",
        repetitions: Optional[int] = None,
        auto_scale: bool = True,
        babble_enabled: bool = True,
        verbose: bool = False,
        **kwargs,
    ):
        # Pass everything to OpenAI
        super().__init__(*args, **kwargs)
        
        self._babble_enabled = babble_enabled
        self._babble_word = babble_word
        self._verbose = verbose
        self._injector = BabbleInjector(
            babble_word=babble_word,
            repetitions=repetitions,
            auto_scale=auto_scale,
        )
        
        # Get original chat before we override it
        original_chat = object.__getattribute__(self, 'chat')
        self._original_chat = original_chat
        self.chat = _ChatProxy(original_chat, self._injector, babble_word, verbose, babble_enabled)
    
    def delegate(
        self,
        messages: list[dict],
        model: str = "gpt-4",
        timeout: Optional[float] = None,
    ) -> str:
        """Delegate to calling agent via FIFO with babble pre/post processing."""
        from . import fifo
        
        modified_messages, match = self._injector.inject(messages)
        if match and self._verbose:
            log.debug(f"Trigger: '{match.original_phrase}'")
        
        response = fifo.delegate_to_agent(modified_messages, model=model, timeout=timeout)
        
        if match:
            response = strip_babble(response, self._babble_word)
        
        return response


class _ChatProxy:
    """
    Minimal proxy for chat namespace.
    
    Only intercepts completions.create(), passes everything else through.
    """
    
    def __init__(self, original_chat: Any, injector: BabbleInjector, babble_word: str, verbose: bool, enabled: bool):
        self._original = original_chat
        self._injector = injector
        self._babble_word = babble_word
        self._verbose = verbose
        self._enabled = enabled
        self.completions = _CompletionsProxy(
            original_chat.completions, 
            injector, 
            babble_word,
            verbose, 
            enabled
        )
    
    def __getattr__(self, name: str) -> Any:
        """Pass through any other attributes to original chat."""
        return getattr(self._original, name)


class _CompletionsProxy:
    """
    Minimal proxy for chat.completions.
    
    Only intercepts create(), passes everything else through.
    """
    
    def __init__(self, original_completions: Any, injector: BabbleInjector, babble_word: str, verbose: bool, enabled: bool):
        self._original = original_completions
        self._injector = injector
        self._babble_word = babble_word
        self._verbose = verbose
        self._enabled = enabled
    
    def create(self, *, messages: list[dict], stream: bool = False, force_babble: Optional[Union[str, list]] = None, **kwargs) -> Any:
        """
        Intercept create() for babble injection.
        
        Pre: inject babble if triggered or forced
        Post: strip babble from response
        
        Args:
            force_babble: Force babble injection with custom phrase
                - str: will be repeated according to injector settings
                - list: will be concatenated as-is (e.g., ["blah"]*100 or ["Count to 100"])
        """
        match = None
        
        # Handle force_babble parameter
        if force_babble is not None:
            # Validate input
            if isinstance(force_babble, list):
                if not force_babble:
                    raise ValueError("force_babble list cannot be empty")
                if not all(isinstance(x, str) for x in force_babble):
                    raise TypeError("force_babble list must contain only strings")
                # List: concatenate without additional repetition
                babble_text = " ".join(force_babble)
            elif isinstance(force_babble, str):
                if not force_babble.strip():
                    raise ValueError("force_babble string cannot be empty")
                # String: repeat according to default settings
                from .triggers import TriggerMatch
                fake_match = TriggerMatch(
                    mode="word",
                    count=1,
                    original_phrase="[forced]",
                    start=0,
                    end=0
                )
                repetitions = self._injector.get_repetitions(fake_match)
                babble_text = " ".join([force_babble] * repetitions)
            else:
                raise TypeError(f"force_babble must be str or list[str], got {type(force_babble).__name__}")
            
            # Escape quotes in babble to prevent prompt injection
            babble_escaped = babble_text.replace('"', '\\"')
            
            # Inject the forced babble
            priming = f'First, copy this text exactly: "{babble_escaped}". Then immediately answer the question that follows.\n\n'
            messages = list(messages)
            if messages and messages[-1].get("role") == "user":
                messages[-1] = {
                    **messages[-1],
                    "content": priming + messages[-1].get("content", "")
                }
            match = True  # Mark as having babble for stripping
            if self._verbose:
                log.debug(f"Forced babble: {len(babble_text.split())} words")
        
        elif self._enabled:
            messages, match = self._injector.inject(list(messages))
            if match and self._verbose:
                log.debug(f"Trigger: '{match.original_phrase}'")
        
        # Call original - pass through ALL kwargs unchanged
        response = self._original.create(messages=messages, stream=stream, **kwargs)
        
        # Strip babble from non-streaming response
        if not stream and match and response.choices:
            content = response.choices[0].message.content
            if content:
                response.choices[0].message.content = strip_babble(content, self._babble_word)
        
        return response
    
    def __getattr__(self, name: str) -> Any:
        """Pass through any other attributes to original completions."""
        return getattr(self._original, name)
