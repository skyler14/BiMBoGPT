"""Tests for CLI."""

import pytest
from click.testing import CliRunner
from bimbogpt.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestHelp:
    """Tests for help output."""
    
    def test_shows_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "BiMBoGPT" in result.output
        assert "Babble In Means Better Out" in result.output


class TestRegister:
    """Tests for registration commands."""
    
    def test_register_none(self, runner):
        result = runner.invoke(main, ["--register", "none"])
        assert result.exit_code == 0
        assert "BiMBoGPT" in result.output
        assert "pip install" in result.output
    
    def test_register_help(self, runner):
        result = runner.invoke(main, ["--register", "help"])
        assert result.exit_code == 0
        assert "Registration" in result.output
    
    def test_register_code_creates_file(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["--register", "code", "-v"])
            assert result.exit_code == 0
            
            with open("CLAUDE.md") as f:
                content = f.read()
            assert "BiMBoGPT" in content
            assert "in 1 word" in content
    
    def test_register_agent_creates_workflow(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["--register", "agent", "-v"])
            assert result.exit_code == 0
            
            with open(".agent/workflows/bimbogpt.md") as f:
                content = f.read()
            assert "description:" in content
            assert "BiMBoGPT" in content
