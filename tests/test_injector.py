"""Tests for babble injection."""

import pytest
from bimbogpt.injector import BabbleInjector
from bimbogpt.triggers import TriggerMatch


@pytest.fixture
def injector():
    return BabbleInjector()


class TestBabbleGeneration:
    """Tests for babble string generation."""
    
    def test_generates_babble(self, injector):
        babble = injector.generate_babble(5)
        assert babble == "blah blah blah blah blah"
    
    def test_custom_babble_word(self):
        custom = BabbleInjector(babble_word="meow")
        babble = custom.generate_babble(3)
        assert babble == "meow meow meow"
    
    def test_fixed_repetitions(self):
        fixed = BabbleInjector(repetitions=10)
        match = TriggerMatch(mode="word", count=1, original_phrase="", start=0, end=0)
        reps = fixed.get_repetitions(match)
        assert reps == 10


class TestMessageInjection:
    """Tests for injecting babble into messages."""
    
    def test_injects_into_triggered_message(self, injector):
        messages = [{"role": "user", "content": "explain in 1 word: hello"}]
        modified, match = injector.inject(messages)
        
        assert match is not None
        assert match.mode == "word"
        assert "blah" in modified[0]["content"]
        assert "explain in 1 word: hello" in modified[0]["content"]
    
    def test_no_injection_without_trigger(self, injector):
        messages = [{"role": "user", "content": "hello world"}]
        modified, match = injector.inject(messages)
        
        assert match is None
        assert modified == messages
    
    def test_only_modifies_last_user_message(self, injector):
        messages = [
            {"role": "user", "content": "in 1 word: first"},  # Has trigger
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "in 1 word: second"},  # Has trigger (last)
        ]
        modified, match = injector.inject(messages)
        
        # Only last user message should be modified
        assert "blah" not in modified[0]["content"]
        assert "blah" in modified[2]["content"]
    
    def test_preserves_message_structure(self, injector):
        messages = [{"role": "user", "content": "in 1 word: test", "name": "tester"}]
        modified, _ = injector.inject(messages)
        
        assert modified[0]["role"] == "user"
        assert modified[0]["name"] == "tester"


class TestAutoScaling:
    """Tests for automatic babble scaling."""
    
    def test_more_babble_for_word_mode(self, injector):
        word_match = TriggerMatch(mode="word", count=1, original_phrase="", start=0, end=0)
        para_match = TriggerMatch(mode="paragraph", count=1, original_phrase="", start=0, end=0)
        
        word_reps = injector.get_repetitions(word_match)
        para_reps = injector.get_repetitions(para_match)
        
        assert word_reps > para_reps
    
    def test_less_babble_for_higher_count(self, injector):
        single = TriggerMatch(mode="sentence", count=1, original_phrase="", start=0, end=0)
        multi = TriggerMatch(mode="sentence", count=5, original_phrase="", start=0, end=0)
        
        single_reps = injector.get_repetitions(single)
        multi_reps = injector.get_repetitions(multi)
        
        assert single_reps > multi_reps


class TestShouldInject:
    """Tests for quick injection check."""
    
    def test_should_inject_true(self, injector):
        messages = [{"role": "user", "content": "explain in 1 word"}]
        assert injector.should_inject(messages) is True
    
    def test_should_inject_false(self, injector):
        messages = [{"role": "user", "content": "hello"}]
        assert injector.should_inject(messages) is False
