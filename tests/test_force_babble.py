"""Tests for force_babble parameter validation."""

import pytest
from unittest.mock import MagicMock, patch


class TestForceBabbleValidation:
    """Tests for force_babble input validation."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock BimboClient for testing validation."""
        with patch('bimbogpt.client.OpenAI'):
            from bimbogpt.client import BimboClient
            client = BimboClient(api_key="test")
            # Mock the original completions to avoid API calls
            client._original_chat.completions.create = MagicMock()
            return client
    
    def test_force_babble_empty_list_raises(self, mock_client):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            mock_client.chat.completions.create(
                model="test",
                messages=[{"role": "user", "content": "test"}],
                force_babble=[]
            )
    
    def test_force_babble_empty_string_raises(self, mock_client):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            mock_client.chat.completions.create(
                model="test",
                messages=[{"role": "user", "content": "test"}],
                force_babble=""
            )
    
    def test_force_babble_whitespace_string_raises(self, mock_client):
        """Whitespace-only string should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            mock_client.chat.completions.create(
                model="test",
                messages=[{"role": "user", "content": "test"}],
                force_babble="   "
            )
    
    def test_force_babble_list_with_non_strings_raises(self, mock_client):
        """List with non-string items should raise TypeError."""
        with pytest.raises(TypeError, match="must contain only strings"):
            mock_client.chat.completions.create(
                model="test",
                messages=[{"role": "user", "content": "test"}],
                force_babble=["valid", 123, "also valid"]
            )
    
    def test_force_babble_invalid_type_raises(self, mock_client):
        """Non-string, non-list types should raise TypeError."""
        with pytest.raises(TypeError, match="must be str or list"):
            mock_client.chat.completions.create(
                model="test",
                messages=[{"role": "user", "content": "test"}],
                force_babble={"key": "value"}
            )
    
    def test_force_babble_valid_list_passes(self, mock_client):
        """Valid list should not raise."""
        mock_client._original_chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="response"))]
        )
        # Should not raise
        mock_client.chat.completions.create(
            model="test",
            messages=[{"role": "user", "content": "test"}],
            force_babble=["blah"] * 10
        )
    
    def test_force_babble_valid_string_passes(self, mock_client):
        """Valid string should not raise."""
        mock_client._original_chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="response"))]
        )
        # Should not raise
        mock_client.chat.completions.create(
            model="test",
            messages=[{"role": "user", "content": "test"}],
            force_babble="meow"
        )
    
    def test_force_babble_quotes_are_escaped(self, mock_client):
        """Quotes in babble should be escaped."""
        mock_client._original_chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="response"))]
        )
        
        mock_client.chat.completions.create(
            model="test",
            messages=[{"role": "user", "content": "test"}],
            force_babble=['Say "hello"']
        )
        
        # Check that the priming prompt has escaped quotes
        call_args = mock_client._original_chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        assert '\\"' in messages[0]['content']
