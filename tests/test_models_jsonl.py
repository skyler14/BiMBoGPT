"""Tests for models.jsonl parsing and validation."""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile


class TestLoadModels:
    """Tests for models.jsonl loading and validation."""
    
    def test_load_valid_jsonl(self, tmp_path):
        """Valid JSONL should load correctly."""
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "test1", "model": "gpt-4", "api_key": "sk-test"}\n'
            '{"name": "test2", "model": "gpt-3.5-turbo", "provider": "openai"}\n'
        )
        
        models = load_models(models_file)
        
        assert len(models) == 2
        assert "test1" in models
        assert "test2" in models
        assert models["test1"].model == "gpt-4"
        assert models["test2"].provider == "openai"
    
    def test_load_skips_comments(self, tmp_path):
        """Lines starting with # should be skipped."""
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '# This is a comment\n'
            '{"name": "test", "model": "gpt-4"}\n'
            '# Another comment\n'
        )
        
        models = load_models(models_file)
        
        assert len(models) == 1
        assert "test" in models
    
    def test_load_skips_empty_lines(self, tmp_path):
        """Empty lines should be skipped."""
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "test", "model": "gpt-4"}\n'
            '\n'
            '   \n'
            '{"name": "test2", "model": "gpt-4"}\n'
        )
        
        models = load_models(models_file)
        
        assert len(models) == 2
    
    def test_load_skips_invalid_json(self, tmp_path, caplog):
        """Invalid JSON lines should be skipped with warning."""
        import logging
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "valid", "model": "gpt-4"}\n'
            'not valid json\n'
            '{"name": "also_valid", "model": "gpt-4"}\n'
        )
        
        with caplog.at_level(logging.WARNING):
            models = load_models(models_file)
        
        assert len(models) == 2
        assert "valid" in models
        assert "also_valid" in models
        assert "invalid JSON" in caplog.text
    
    def test_load_skips_missing_name(self, tmp_path, caplog):
        """Lines missing 'name' should be skipped with warning."""
        import logging
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"model": "gpt-4"}\n'
            '{"name": "valid", "model": "gpt-4"}\n'
        )
        
        with caplog.at_level(logging.WARNING):
            models = load_models(models_file)
        
        assert len(models) == 1
        assert "valid" in models
        assert "missing required 'name'" in caplog.text
    
    def test_load_skips_missing_model(self, tmp_path, caplog):
        """Lines missing 'model' should be skipped with warning."""
        import logging
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "invalid"}\n'
            '{"name": "valid", "model": "gpt-4"}\n'
        )
        
        with caplog.at_level(logging.WARNING):
            models = load_models(models_file)
        
        assert len(models) == 1
        assert "valid" in models
        assert "missing required 'model'" in caplog.text
    
    def test_load_warns_on_duplicate_names(self, tmp_path, caplog):
        """Duplicate names should warn and use last value."""
        import logging
        from bimbogpt.models import load_models
        
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "dupe", "model": "gpt-4"}\n'
            '{"name": "dupe", "model": "gpt-3.5-turbo"}\n'
        )
        
        with caplog.at_level(logging.WARNING):
            models = load_models(models_file)
        
        assert len(models) == 1
        assert models["dupe"].model == "gpt-3.5-turbo"  # Last one wins
        assert "duplicate name" in caplog.text
    
    def test_load_nonexistent_file(self):
        """Nonexistent file should return empty dict."""
        from bimbogpt.models import load_models
        
        models = load_models(Path("/nonexistent/path/models.jsonl"))
        
        assert models == {}


class TestListModels:
    """Tests for list_models function."""
    
    def test_list_models_returns_names(self, tmp_path, monkeypatch):
        """list_models should return list of model names."""
        from bimbogpt import models
        
        # Patch find_models_file to use our temp file
        models_file = tmp_path / "models.jsonl"
        models_file.write_text(
            '{"name": "model1", "model": "gpt-4"}\n'
            '{"name": "model2", "model": "gpt-3.5-turbo"}\n'
        )
        monkeypatch.setattr(models, "find_models_file", lambda: models_file)
        
        names = models.list_models()
        
        assert set(names) == {"model1", "model2"}
