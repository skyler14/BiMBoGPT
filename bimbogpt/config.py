"""
Configuration for BiMBoGPT.

Supports:
- Runtime configuration via constructor args
- Config file for agentic installs (~/.bimbogpt/config.toml)
- Environment variables
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_PATH = Path.home() / ".bimbogpt" / "config.toml"

DEFAULT_CONFIG = """
# BiMBoGPT Configuration
# Tune these settings for your use case

[babble]
# The word to repeat for babble priming
word = "blah"

# Number of repetitions (null = auto-scale based on trigger)
repetitions = null

# Auto-scale repetitions based on output mode (word/sentence/paragraph)
auto_scale = true

[stripping]
# Threshold for considering a line as babble (0.0-1.0)
# Lower = more aggressive stripping
threshold = 0.4

# Levenshtein distance tolerance for typo detection
typo_tolerance = 2

[agent]
# Default model for FIFO delegation
default_model = "gpt-4"
"""


@dataclass
class BabbleConfig:
    """Babble injection configuration."""
    word: str = "blah"
    repetitions: Optional[int] = None
    auto_scale: bool = True


@dataclass
class StrippingConfig:
    """Babble stripping configuration."""
    threshold: float = 0.4
    typo_tolerance: int = 2


@dataclass
class AgentConfig:
    """Agent/FIFO configuration."""
    default_model: str = "gpt-4"


@dataclass
class Config:
    """Full BiMBoGPT configuration."""
    babble: BabbleConfig = field(default_factory=BabbleConfig)
    stripping: StrippingConfig = field(default_factory=StrippingConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load config from file, falling back to defaults."""
        path = path or DEFAULT_CONFIG_PATH
        
        if not path.exists():
            return cls()
        
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            
            return cls(
                babble=BabbleConfig(
                    word=data.get("babble", {}).get("word", "blah"),
                    repetitions=data.get("babble", {}).get("repetitions"),
                    auto_scale=data.get("babble", {}).get("auto_scale", True),
                ),
                stripping=StrippingConfig(
                    threshold=data.get("stripping", {}).get("threshold", 0.4),
                    typo_tolerance=data.get("stripping", {}).get("typo_tolerance", 2),
                ),
                agent=AgentConfig(
                    default_model=data.get("agent", {}).get("default_model", "gpt-4"),
                ),
            )
        except Exception:
            return cls()
    
    @staticmethod
    def init_config(path: Optional[Path] = None) -> Path:
        """Create default config file."""
        path = path or DEFAULT_CONFIG_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG.strip())
        return path


# Singleton for global config
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config, loading from file if not yet loaded."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config(path: Optional[Path] = None) -> Config:
    """Reload config from file."""
    global _config
    _config = Config.load(path)
    return _config
