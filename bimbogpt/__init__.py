"""
BiMBoGPT - Babble In Means Better Out

Just change your import:
    from openai import OpenAI  →  from bimbogpt import OpenAI

Everything else stays the same.
"""

from .client import BimboClient

# The main export - just change "from openai" to "from bimbogpt"
OpenAI = BimboClient

from .injector import BabbleInjector
from .triggers import TriggerDetector, TriggerMatch
from .fifo import delegate_to_agent

__all__ = [
    "OpenAI",           # Primary export - drop-in replacement
    "BimboClient",      # Alias for explicit usage
    "BabbleInjector", 
    "TriggerDetector",
    "TriggerMatch",
    "delegate_to_agent",
]

__version__ = "0.1.0"
