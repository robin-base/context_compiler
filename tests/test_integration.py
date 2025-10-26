from pathlib import Path
from unittest.mock import patch

import pytest

from context_compiler.compiler import ContextCompiler


def test_context_compiler_init():
    """Test initializing ContextCompiler."""
    vault_path = Path("tests/fixtures/test_vault")
    compiler = ContextCompiler(vault_path, vault_name="TestVault")

    assert compiler.vault_path == vault_path
    assert compiler.vault_name == "TestVault"


def test_compile_context_end_to_end():
    """Test full context compilation flow."""
    vault_path = Path("tests/fixtures/test_vault")
    compiler = ContextCompiler(vault_path, vault_name="TestVault")

    # Mock LLM calls
    mock_categorization = "1. VERY_RELEVANT - Recent meeting note"
    mock_summary = "You have a recent meeting with Sarah."

    with patch('context_compiler.ranking.RankingService._call_llm', return_value=mock_categorization):
        with patch('context_compiler.brief.BriefGenerator._generate_summary', return_value=mock_summary):
            brief = compiler.compile_context("meeting with Sarah")

    # Should generate complete brief
    assert "# Prep for meeting with Sarah" in brief
    assert "## Summary" in brief
    assert mock_summary in brief
    assert "Sarah" in brief


def test_compile_context_no_results():
    """Test handling no matching notes."""
    vault_path = Path("tests/fixtures/test_vault")
    compiler = ContextCompiler(vault_path, vault_name="TestVault")

    brief = compiler.compile_context("nonexistent topic xyz123")

    assert "No notes found" in brief
