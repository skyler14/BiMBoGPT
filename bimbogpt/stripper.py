"""
Babble stripping utilities.

Handles imperfect reproduction of babble words by models:
- Capitalization: "Blah", "BLAH"
- Punctuation: "blah.", "blah,", "blah!"
- Typos: "blsh", "blaah", "blahh"
- Variations: "blahblah", "blah-blah"
"""

import re
from typing import Optional


def normalize_word(word: str) -> str:
    """Strip punctuation and lowercase."""
    return re.sub(r'[^\w]', '', word).lower()


def is_babble_like(word: str, babble_word: str, tolerance: int = 2) -> bool:
    """
    Check if word is close enough to babble word.
    
    Uses simple edit distance approximation for typo tolerance.
    """
    normalized = normalize_word(word)
    
    if not normalized:
        return False
    
    # Exact match
    if normalized == babble_word:
        return True
    
    # Repeated babble (e.g., "blahblah")
    if babble_word in normalized and len(normalized) <= len(babble_word) * 2 + 1:
        return True
    
    # Length check - if too different, skip expensive edit distance
    if abs(len(normalized) - len(babble_word)) > tolerance:
        return False
    
    # Simple edit distance (insertions, deletions, substitutions)
    distance = levenshtein_distance(normalized, babble_word)
    return distance <= tolerance


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_babble_ratio(line: str, babble_word: str) -> float:
    """Calculate what fraction of words in a line are babble-like."""
    words = line.split()
    if not words:
        return 0.0
    
    babble_count = sum(1 for w in words if is_babble_like(w, babble_word))
    return babble_count / len(words)


def strip_babble(content: str, babble_word: str = "blah", threshold: float = 0.4) -> str:
    """
    Strip babble from response content.
    
    Resilient to:
    - Capitalization variations
    - Punctuation
    - Minor typos (1-2 character edits)
    - Repeated/concatenated babble
    
    Args:
        content: Response text
        babble_word: The babble word to detect (default: "blah")
        threshold: Lines with this fraction+ of babble words are stripped
        
    Returns:
        Content with babble removed
    """
    if not content:
        return content
    
    lines = content.split('\n')
    result_lines = []
    in_babble_section = True
    
    for line in lines:
        stripped = line.strip()
        
        # Empty lines don't break babble section
        if not stripped:
            if not in_babble_section:
                result_lines.append(line)
            continue
        
        # Check babble ratio
        ratio = calculate_babble_ratio(stripped, babble_word)
        
        if ratio >= threshold:
            # This line is babble, skip it
            continue
        else:
            # Real content - we're past the babble section
            in_babble_section = False
            result_lines.append(line)
    
    return '\n'.join(result_lines).strip()
