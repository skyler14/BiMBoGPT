"""
Trigger detection for babble injection.

Broadly detects phrases requesting concise output:
- "in X word/sentence/paragraph" 
- "X word answer", "one-word response"
- "answer in X words"
- "X words only", "one word only"
- Explicit babble flag: [babble] or --babble
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

# Regex for numbers (digit or word)
NUM_PATTERN = r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|single)'

# Mode words
MODE_PATTERN = r'(words?|sentences?|paragraphs?)'


@dataclass
class TriggerMatch:
    """Result of a trigger detection."""
    mode: str  # "word", "sentence", or "paragraph"
    count: int
    original_phrase: str
    start: int
    end: int


class TriggerDetector:
    """
    Detects trigger phrases that should activate babble injection.
    
    Patterns detected:
    - "in X word(s)" / "in X sentence(s)" / "in X paragraph(s)"
    - "X word answer" / "one-word response" / "single word reply"
    - "answer in X words" / "respond in X sentences"
    - "X words only" / "one word only"
    - "[babble]" or "--babble" explicit flag
    """
    
    # Build comprehensive patterns
    PATTERNS = [
        # "in X word(s)" - original pattern
        re.compile(rf'\bin\s+{NUM_PATTERN}\s+{MODE_PATTERN}\b', re.IGNORECASE),
        
        # "X word answer/response/reply"
        re.compile(rf'\b{NUM_PATTERN}[\s-]+{MODE_PATTERN}\s+(answer|response|reply)\b', re.IGNORECASE),
        
        # "answer/respond/reply in X word(s)"
        re.compile(rf'\b(answer|respond|reply)\s+in\s+{NUM_PATTERN}\s+{MODE_PATTERN}\b', re.IGNORECASE),
        
        # "X word(s) only" / "only X word(s)"
        re.compile(rf'\b{NUM_PATTERN}\s+{MODE_PATTERN}\s+only\b', re.IGNORECASE),
        re.compile(rf'\bonly\s+{NUM_PATTERN}\s+{MODE_PATTERN}\b', re.IGNORECASE),
        
        # "X-word" (hyphenated, like "one-word")
        re.compile(rf'\b{NUM_PATTERN}-{MODE_PATTERN}\b', re.IGNORECASE),
    ]
    
    # Explicit babble flag
    BABBLE_FLAG = re.compile(r'\[babble\]|--babble', re.IGNORECASE)
    
    # Quick trigger patterns (no count extraction needed)
    QUICK_TRIGGERS = [
        (re.compile(r'\b(tldr|tl;dr)\b', re.IGNORECASE), "word", 1),
        (re.compile(r'\bgimme the gist\b', re.IGNORECASE), "sentence", 1),
        (re.compile(r'\bsummarize\b', re.IGNORECASE), "sentence", 2),
        (re.compile(r'\bbriefly\b', re.IGNORECASE), "sentence", 2),
        (re.compile(r'\bconcisely\b', re.IGNORECASE), "sentence", 2),
        (re.compile(r'\bshort answer\b', re.IGNORECASE), "sentence", 1),
    ]
    
    def _parse_count(self, count_str: str) -> int:
        """Parse a number string to int."""
        count_str = count_str.lower()
        if count_str.isdigit():
            return int(count_str)
        return WORD_TO_NUM.get(count_str, 1)
    
    def _parse_mode(self, mode_str: str) -> str:
        """Normalize mode string."""
        return mode_str.lower().rstrip('s')
    
    def _extract_from_match(self, match: re.Match, text: str) -> Optional[TriggerMatch]:
        """Extract count and mode from regex match groups."""
        groups = match.groups()
        
        count = None
        mode = None
        
        for g in groups:
            if g is None:
                continue
            g_lower = g.lower()
            
            # Check if it's a number
            if g_lower.isdigit() or g_lower in WORD_TO_NUM:
                count = self._parse_count(g_lower)
            # Check if it's a mode
            elif g_lower.rstrip('s') in ('word', 'sentence', 'paragraph'):
                mode = self._parse_mode(g_lower)
        
        if count is not None and mode is not None:
            return TriggerMatch(
                mode=mode,
                count=count,
                original_phrase=match.group(0),
                start=match.start(),
                end=match.end(),
            )
        
        return None
    
    def detect(self, text: str) -> Optional[TriggerMatch]:
        """
        Detect a trigger phrase in the text.
        
        Returns TriggerMatch if found, None otherwise.
        """
        # Check explicit babble flag first
        flag_match = self.BABBLE_FLAG.search(text)
        if flag_match:
            return TriggerMatch(
                mode="word",
                count=1,
                original_phrase=flag_match.group(0),
                start=flag_match.start(),
                end=flag_match.end(),
            )
        
        # Check comprehensive patterns
        for pattern in self.PATTERNS:
            match = pattern.search(text)
            if match:
                result = self._extract_from_match(match, text)
                if result:
                    return result
        
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
