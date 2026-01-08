"""Tests for TriggerMatch validation."""

import pytest
from bimbogpt.triggers import TriggerMatch


class TestTriggerMatchValidation:
    """Tests for TriggerMatch __post_init__ validation."""
    
    def test_valid_match_passes(self):
        """Valid TriggerMatch should not raise."""
        match = TriggerMatch(
            mode="word",
            count=1,
            original_phrase="in 1 word",
            start=0,
            end=9
        )
        assert match.mode == "word"
        assert match.count == 1
    
    def test_count_zero_raises(self):
        """count < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="count must be >= 1"):
            TriggerMatch(
                mode="word",
                count=0,
                original_phrase="test",
                start=0,
                end=4
            )
    
    def test_count_negative_raises(self):
        """Negative count should raise ValueError."""
        with pytest.raises(ValueError, match="count must be >= 1"):
            TriggerMatch(
                mode="word",
                count=-5,
                original_phrase="test",
                start=0,
                end=4
            )
    
    def test_invalid_mode_raises(self):
        """Invalid mode should raise ValueError."""
        with pytest.raises(ValueError, match="mode must be one of"):
            TriggerMatch(
                mode="invalid",
                count=1,
                original_phrase="test",
                start=0,
                end=4
            )
    
    def test_start_greater_than_end_raises(self):
        """start > end should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be greater than end"):
            TriggerMatch(
                mode="word",
                count=1,
                original_phrase="test",
                start=10,
                end=5
            )
    
    def test_all_valid_modes(self):
        """All valid modes should pass."""
        for mode in ("word", "sentence", "paragraph"):
            match = TriggerMatch(
                mode=mode,
                count=1,
                original_phrase="test",
                start=0,
                end=4
            )
            assert match.mode == mode
    
    def test_start_equals_end_passes(self):
        """start == end should be valid."""
        match = TriggerMatch(
            mode="word",
            count=1,
            original_phrase="x",
            start=5,
            end=5
        )
        assert match.start == match.end
