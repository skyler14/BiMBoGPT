"""Tests for trigger detection."""

import pytest
from bimbogpt.triggers import TriggerDetector, TriggerMatch


@pytest.fixture
def detector():
    return TriggerDetector()


class TestInXPattern:
    """Tests for 'in X word/sentence/paragraph' patterns."""
    
    @pytest.mark.parametrize("text,expected_mode,expected_count", [
        ("answer in 1 word", "word", 1),
        ("explain in one word", "word", 1),
        ("describe in 2 sentences", "sentence", 2),
        ("summarize in two sentences", "sentence", 2),
        ("write in 3 paragraphs", "paragraph", 3),
        ("respond in three paragraphs", "paragraph", 3),
        ("In 5 words please", "word", 5),
        ("explain IN ONE WORD", "word", 1),  # Case insensitive
    ])
    def test_detects_in_x_pattern(self, detector, text, expected_mode, expected_count):
        match = detector.detect(text)
        
        assert match is not None
        assert match.mode == expected_mode
        assert match.count == expected_count
    
    def test_handles_singular_and_plural(self, detector):
        singular = detector.detect("in 1 word")
        plural = detector.detect("in 2 words")
        
        assert singular.mode == "word"
        assert plural.mode == "word"


class TestQuickTriggers:
    """Tests for quick trigger phrases."""
    
    @pytest.mark.parametrize("text", [
        "give me the tldr",
        "TLDR please",
        "tl;dr",
    ])
    def test_detects_tldr(self, detector, text):
        match = detector.detect(text)
        assert match is not None
        assert match.mode == "word"
    
    def test_detects_gimme_the_gist(self, detector):
        match = detector.detect("gimme the gist of this document")
        assert match is not None
        assert match.mode == "sentence"
    
    def test_detects_summarize(self, detector):
        match = detector.detect("please summarize this article")
        assert match is not None
        assert match.mode == "sentence"


class TestNoMatch:
    """Tests for texts that should not trigger."""
    
    @pytest.mark.parametrize("text", [
        "hello world",
        "explain this to me",
        "what is the meaning of life",
        "in the beginning",  # Not followed by count + mode
        "word for word",
    ])
    def test_no_false_positives(self, detector, text):
        match = detector.detect(text)
        assert match is None


class TestHasTrigger:
    """Tests for quick trigger check."""
    
    def test_has_trigger_true(self, detector):
        assert detector.has_trigger("explain in 1 word") is True
    
    def test_has_trigger_false(self, detector):
        assert detector.has_trigger("hello world") is False
