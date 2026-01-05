"""
BiMBoGPT - Babble In Means Better Out

Drop-in replacement for OpenAI client that injects babble priming
to help models produce better reasoning chains.

Usage:
    from bimbogpt import BimboClient
    
    client = BimboClient()  # Uses OPENAI_API_KEY from env
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Summarize this in 1 word: ..."}]
    )
"""

from .client import BimboClient
from .injector import BabbleInjector
from .triggers import TriggerDetector, TriggerMatch
from .fifo import delegate_to_agent

__all__ = [
    "BimboClient",
    "BabbleInjector", 
    "TriggerDetector",
    "TriggerMatch",
    "delegate_to_agent",
]

__version__ = "0.1.0"
