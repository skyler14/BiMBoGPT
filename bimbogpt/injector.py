"""
Babble injection for message priming.

Injects filler text ("blah blah blah...") into prompts to prime
models for longer reasoning chains before giving concise answers.
"""

from typing import Optional
from .triggers import TriggerDetector, TriggerMatch


class BabbleInjector:
    """
    Injects babble priming into chat messages.
    
    The key insight: asking models to copy filler text forces them to
    "show their work" before answering, producing better reasoning chains.
    """
    
    # Default babble configurations by mode
    # Reduced for faster API responses; increase for more thorough priming
    DEFAULT_REPETITIONS = {
        "word": 20,       # Terser outputs get more babble
        "sentence": 15,
        "paragraph": 10,
    }
    
    def __init__(
        self,
        babble_word: str = "blah",
        repetitions: Optional[int] = None,
        auto_scale: bool = True,
    ):
        """
        Initialize the babble injector.
        
        Args:
            babble_word: The word to repeat (default: "blah")
            repetitions: Fixed number of repetitions (overrides auto_scale)
            auto_scale: If True, adjust repetitions based on trigger mode
        """
        self.babble_word = babble_word
        self.fixed_repetitions = repetitions
        self.auto_scale = auto_scale
        self.detector = TriggerDetector()
    
    def generate_babble(self, count: int) -> str:
        """Generate babble string with specified repetitions."""
        return " ".join([self.babble_word] * count)
    
    def get_repetitions(self, match: TriggerMatch) -> int:
        """Determine number of babble repetitions based on trigger."""
        if self.fixed_repetitions is not None:
            return self.fixed_repetitions
        
        if not self.auto_scale:
            return 100  # Default fallback
        
        # More babble for terser expected outputs
        base = self.DEFAULT_REPETITIONS.get(match.mode, 100)
        
        # Scale inversely with count (fewer words = more babble needed)
        if match.count <= 1:
            return base
        elif match.count <= 3:
            return int(base * 0.75)
        else:
            return int(base * 0.5)
    
    def create_priming_instruction(self, babble: str) -> str:
        """Create the priming instruction to prepend."""
        return (
            f'First, copy this text exactly: "{babble}". '
            f"Then immediately answer the question that follows.\n\n"
        )
    
    def inject_into_message(self, content: str, match: TriggerMatch) -> str:
        """Inject babble priming into a single message."""
        repetitions = self.get_repetitions(match)
        babble = self.generate_babble(repetitions)
        priming = self.create_priming_instruction(babble)
        return priming + content
    
    def inject(self, messages: list[dict]) -> tuple[list[dict], Optional[TriggerMatch]]:
        """
        Process messages and inject babble priming if triggered.
        
        Args:
            messages: OpenAI-style message list
            
        Returns:
            Tuple of (modified_messages, trigger_match or None)
        """
        if not messages:
            return messages, None
        
        # Find the last user message
        last_user_idx = None
        for i, msg in enumerate(reversed(messages)):
            if msg.get("role") == "user":
                last_user_idx = len(messages) - 1 - i
                break
        
        if last_user_idx is None:
            return messages, None
        
        user_content = messages[last_user_idx].get("content", "")
        
        # Handle string content
        if isinstance(user_content, str):
            match = self.detector.detect(user_content)
            if match:
                modified = messages.copy()
                modified[last_user_idx] = {
                    **messages[last_user_idx],
                    "content": self.inject_into_message(user_content, match),
                }
                return modified, match
        
        return messages, None
    
    def should_inject(self, messages: list[dict]) -> bool:
        """Quick check if messages contain a trigger."""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and self.detector.has_trigger(content):
                    return True
        return False
