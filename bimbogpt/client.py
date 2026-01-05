"""
Drop-in replacement for OpenAI client with babble injection.

DESIGN: Minimal interception, maximum forward compatibility.
- Inherits from OpenAI
- Only intercepts chat.completions.create()
- All other methods/attributes pass through unchanged
- Uses __getattr__ for full compatibility with future SDK changes
"""

from typing import Optional, Any
from openai import OpenAI

from .injector import BabbleInjector
from .stripper import strip_babble


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
        
        # Wrap only the chat completions endpoint
        self._original_chat = super().chat
        self.chat = _ChatProxy(self._original_chat, self._injector, babble_word, verbose, babble_enabled)
    
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
            print(f"[BiMBoGPT] Trigger: '{match.original_phrase}'")
        
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
    
    def create(self, *, messages: list[dict], stream: bool = False, **kwargs) -> Any:
        """
        Intercept create() for babble injection.
        
        Pre: inject babble if triggered
        Post: strip babble from response
        """
        match = None
        
        if self._enabled:
            messages, match = self._injector.inject(list(messages))
            if match and self._verbose:
                print(f"[BiMBoGPT] Trigger: '{match.original_phrase}'")
        
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
