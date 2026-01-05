"""
Configuration for BiMBoGPT.

Priority (highest to lowest):
1. Constructor arguments
2. Environment variables (BIMBOGPT_*)
3. Config file (~/.bimbogpt/config.toml)
4. Defaults
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_PATH = Path.home() / ".bimbogpt" / "config.toml"

# Environment variable names
ENV_PREFIX = "BIMBOGPT_"
ENV_WORD = f"{ENV_PREFIX}WORD"
ENV_REPETITIONS = f"{ENV_PREFIX}REPETITIONS"
ENV_AUTO_SCALE = f"{ENV_PREFIX}AUTO_SCALE"
ENV_THRESHOLD = f"{ENV_PREFIX}THRESHOLD"
ENV_TYPO_TOLERANCE = f"{ENV_PREFIX}TYPO_TOLERANCE"
ENV_MODEL = f"{ENV_PREFIX}MODEL"

DEFAULT_CONFIG = """
# BiMBoGPT Configuration
# Tune these settings for your use case
# Environment variables (BIMBOGPT_*) override these values

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


def _env_str(key: str, default: str) -> str:
    """Get string from env, with default."""
    return os.environ.get(key, default)


def _env_int(key: str, default: Optional[int]) -> Optional[int]:
    """Get int from env, with default."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    """Get float from env, with default."""
    val = os.environ.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    """Get bool from env, with default."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes", "on")


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
        """
        Load config with priority: env vars > file > defaults.
        """
        path = path or DEFAULT_CONFIG_PATH
        
        # Start with defaults
        file_data = {}
        
        # Load from file if exists
        if path.exists():
            try:
                with open(path, "rb") as f:
                    file_data = tomllib.load(f)
            except Exception:
                pass
        
        # Build config: file values, then env var overrides
        babble_file = file_data.get("babble", {})
        stripping_file = file_data.get("stripping", {})
        agent_file = file_data.get("agent", {})
        
        return cls(
            babble=BabbleConfig(
                word=_env_str(ENV_WORD, babble_file.get("word", "blah")),
                repetitions=_env_int(ENV_REPETITIONS, babble_file.get("repetitions")),
                auto_scale=_env_bool(ENV_AUTO_SCALE, babble_file.get("auto_scale", True)),
            ),
            stripping=StrippingConfig(
                threshold=_env_float(ENV_THRESHOLD, stripping_file.get("threshold", 0.4)),
                typo_tolerance=_env_int(ENV_TYPO_TOLERANCE, stripping_file.get("typo_tolerance", 2)) or 2,
            ),
            agent=AgentConfig(
                default_model=_env_str(ENV_MODEL, agent_file.get("default_model", "gpt-4")),
            ),
        )
    
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
