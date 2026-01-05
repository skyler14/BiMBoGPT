"""
Drop-in replacement for OpenAI client with babble injection.

Inherits from OpenAI and adds pre/post processing for babble.

Usage:
    # Just change your import:
    from bimbogpt import BimboClient as OpenAI
    
    client = OpenAI()
    # Everything works the same, babble is automatic
    
    # For agentic delegation:
    response = client.delegate(messages)  # Uses FIFO to calling agent
"""

from typing import Optional, Any
from openai import OpenAI
from openai._streaming import Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .injector import BabbleInjector
from .triggers import TriggerMatch
from . import fifo


class _BimboChatCompletions:
    """Chat completions with babble pre/post processing."""
    
    def __init__(self, original_completions: Any, injector: BabbleInjector, verbose: bool):
        self._completions = original_completions
        self._injector = injector
        self._verbose = verbose
        self._last_match: Optional[TriggerMatch] = None
    
    def _strip_babble_from_response(self, content: str) -> str:
        """Remove the copied babble from the model's response."""
        from .stripper import strip_babble
        return strip_babble(content, self._injector.babble_word)

    
    def create(
        self,
        messages: list[dict],
        stream: bool = False,
        **kwargs
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Create chat completion with automatic babble injection."""
        # Pre-process: inject babble
        modified_messages, match = self._injector.inject(messages)
        self._last_match = match
        
        if match and self._verbose:
            print(f"[BiMBoGPT] Trigger: '{match.original_phrase}' → injecting babble")
        
        # Call original
        response = self._completions.create(messages=modified_messages, stream=stream, **kwargs)
        
        # Post-process: strip babble from non-streaming response
        if not stream and match and response.choices:
            content = response.choices[0].message.content
            if content:
                cleaned = self._strip_babble_from_response(content)
                response.choices[0].message.content = cleaned
        
        return response


class _BimboChat:
    """Chat namespace with babble-aware completions."""
    
    def __init__(self, original_chat: Any, injector: BabbleInjector, verbose: bool):
        self.completions = _BimboChatCompletions(
            original_chat.completions, 
            injector, 
            verbose
        )


class BimboClient(OpenAI):
    """
    OpenAI client with automatic babble injection.
    
    Inherits from OpenAI - use it exactly the same way.
    Just change your import and everything works.
    
    Example:
        from bimbogpt import BimboClient as OpenAI
        
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Answer in 1 word: ..."}]
        )
        
        # For agentic mode (delegates to calling agent via FIFO):
        response = client.delegate(messages, model="gpt-4")
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
        super().__init__(*args, **kwargs)
        
        self._babble_enabled = babble_enabled
        self._verbose = verbose
        self._injector = BabbleInjector(
            babble_word=babble_word,
            repetitions=repetitions,
            auto_scale=auto_scale,
        )
        
        # Wrap chat.completions with our pre/post processing
        if babble_enabled:
            self.chat = _BimboChat(super().chat, self._injector, verbose)
    
    # -------------------------------------------------------------------------
    # Agentic delegation methods
    # -------------------------------------------------------------------------
    
    def delegate(
        self,
        messages: list[dict],
        model: str = "gpt-4",
        timeout: Optional[float] = None,
    ) -> str:
        """
        Delegate query to calling agent via FIFO.
        
        Use this when running as a subprocess of an AI agent.
        The agent will make the LLM call using its own API key.
        
        Pre-processing: Injects babble if triggers detected.
        Post-processing: Strips babble from response.
        
        Args:
            messages: OpenAI-style messages
            model: Model hint for agent
            timeout: Optional timeout
            
        Returns:
            Clean response string (babble stripped)
        """
        # Pre-process: inject babble
        modified_messages, match = self._injector.inject(messages)
        
        if match and self._verbose:
            print(f"[BiMBoGPT] Trigger: '{match.original_phrase}' → injecting babble")
        
        # Delegate to agent
        response = fifo.delegate_to_agent(modified_messages, model=model, timeout=timeout)
        
        # Post-process: strip babble
        if match:
            response = self._strip_babble(response)
        
        return response
    
    def _strip_babble(self, content: str) -> str:
        """Strip babble from a response string (fuzzy matching)."""
        from .stripper import strip_babble
        return strip_babble(content, self._injector.babble_word)
