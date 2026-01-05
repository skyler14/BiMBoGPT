"""Tests for babble stripping."""

import pytest
from bimbogpt.stripper import (
    strip_babble,
    is_babble_like,
    calculate_babble_ratio,
    levenshtein_distance,
)


class TestIsBabbleLike:
    """Tests for fuzzy babble detection."""
    
    def test_exact_match(self):
        assert is_babble_like("blah", "blah") is True
    
    def test_capitalization(self):
        assert is_babble_like("Blah", "blah") is True
        assert is_babble_like("BLAH", "blah") is True
        assert is_babble_like("BlAh", "blah") is True
    
    def test_punctuation(self):
        assert is_babble_like("blah.", "blah") is True
        assert is_babble_like("blah,", "blah") is True
        assert is_babble_like("blah!", "blah") is True
        assert is_babble_like('"blah"', "blah") is True
    
    def test_typos(self):
        # 1 character off
        assert is_babble_like("blsh", "blah") is True
        assert is_babble_like("blaah", "blah") is True
        assert is_babble_like("blahh", "blah") is True
        assert is_babble_like("blh", "blah") is True
        # 2 characters off
        assert is_babble_like("blhh", "blah") is True
    
    def test_repeated(self):
        assert is_babble_like("blahblah", "blah") is True
    
    def test_not_babble(self):
        assert is_babble_like("hello", "blah") is False
        assert is_babble_like("something", "blah") is False
        assert is_babble_like("Paris", "blah") is False


class TestLevenshtein:
    """Tests for edit distance calculation."""
    
    def test_same_strings(self):
        assert levenshtein_distance("blah", "blah") == 0
    
    def test_one_edit(self):
        assert levenshtein_distance("blah", "blsh") == 1
        assert levenshtein_distance("blah", "blaah") == 1
        assert levenshtein_distance("blah", "blh") == 1
    
    def test_two_edits(self):
        assert levenshtein_distance("blah", "bl") == 2


class TestBabbleRatio:
    """Tests for line babble ratio."""
    
    def test_all_babble(self):
        ratio = calculate_babble_ratio("blah blah blah blah", "blah")
        assert ratio == 1.0
    
    def test_mostly_babble(self):
        ratio = calculate_babble_ratio("blah blah blah word", "blah")
        assert ratio == 0.75
    
    def test_mixed_with_typos(self):
        ratio = calculate_babble_ratio("blah Blah blsh blahh", "blah")
        assert ratio == 1.0  # All are babble-like
    
    def test_no_babble(self):
        ratio = calculate_babble_ratio("hello world something different", "blah")
        assert ratio == 0.0


class TestStripBabble:
    """Tests for full babble stripping."""
    
    def test_strips_babble_prefix(self):
        content = "blah blah blah blah blah\n\nParis"
        result = strip_babble(content)
        assert result == "Paris"
    
    def test_handles_capitalization(self):
        content = "Blah BLAH blah Blah\n\nThe answer is: Paris"
        result = strip_babble(content)
        assert result == "The answer is: Paris"
    
    def test_handles_punctuation(self):
        content = "blah, blah. blah! blah?\n\nParis"
        result = strip_babble(content)
        assert result == "Paris"
    
    def test_handles_typos(self):
        content = "blah blsh blaah blahh blh\n\nParis"
        result = strip_babble(content)
        assert result == "Paris"
    
    def test_preserves_content_with_blah(self):
        # If "blah" appears in real content, should keep it
        content = "blah blah blah\n\nHe said 'blah' sarcastically. Paris."
        result = strip_babble(content)
        assert "Paris" in result
        assert "sarcastically" in result
    
    def test_multi_line_babble(self):
        content = """blah blah blah blah blah blah blah blah blah blah
blah blah blah blah blah blah blah blah blah blah
blah blah blah blah blah blah blah blah blah blah

The capital of France is Paris."""
        result = strip_babble(content)
        assert result == "The capital of France is Paris."
    
    def test_empty_content(self):
        assert strip_babble("") == ""
        assert strip_babble(None) is None
    
    def test_no_babble_content(self):
        content = "The answer is Paris."
        result = strip_babble(content)
        assert result == "The answer is Paris."
