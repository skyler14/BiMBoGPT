"""
Trigger detection for babble injection.

Detects phrases like:
- "in 1 word", "in one word"
- "in 2 sentences", "in two sentences"  
- "in 3 paragraphs", "in three paragraphs"
- "tldr", "gimme the gist", "summarize"
"""

import re
from dataclasses import dataclass
from typing import Optional

# Number words to digits
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a": 1, "single": 1,
}


@dataclass
class TriggerMatch:
    """Result of a trigger detection."""
    mode: str  # "word", "sentence", or "paragraph"
    count: int
    original_phrase: str
    start: int
    end: int


class TriggerDetector:
    """Detects trigger phrases that should activate babble injection."""
    
    # Pattern: "in X word(s)/sentence(s)/paragraph(s)"
    IN_X_PATTERN = re.compile(
        r'\bin\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|single)\s+'
        r'(words?|sentences?|paragraphs?)\b',
        re.IGNORECASE
    )
    
    # Quick trigger patterns
    QUICK_TRIGGERS = [
        (re.compile(r'\b(tldr|tl;dr)\b', re.IGNORECASE), "word", 1),
        (re.compile(r'\bgimme the gist\b', re.IGNORECASE), "sentence", 1),
        (re.compile(r'\bsummarize\b', re.IGNORECASE), "sentence", 2),
        (re.compile(r'\bbriefly\b', re.IGNORECASE), "sentence", 2),
    ]
    
    def detect(self, text: str) -> Optional[TriggerMatch]:
        """
        Detect a trigger phrase in the text.
        
        Returns TriggerMatch if found, None otherwise.
        """
        # Check "in X words/sentences/paragraphs" pattern first
        match = self.IN_X_PATTERN.search(text)
        if match:
            count_str = match.group(1).lower()
            mode_str = match.group(2).lower()
            
            # Parse count
            if count_str.isdigit():
                count = int(count_str)
            else:
                count = WORD_TO_NUM.get(count_str, 1)
            
            # Normalize mode (remove plural 's')
            mode = mode_str.rstrip('s')
            
            return TriggerMatch(
                mode=mode,
                count=count,
                original_phrase=match.group(0),
                start=match.start(),
                end=match.end(),
            )
        
        # Check quick triggers
        for pattern, mode, count in self.QUICK_TRIGGERS:
            match = pattern.search(text)
            if match:
                return TriggerMatch(
                    mode=mode,
                    count=count,
                    original_phrase=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
        
        return None
    
    def has_trigger(self, text: str) -> bool:
        """Quick check if text contains any trigger."""
        return self.detect(text) is not None
