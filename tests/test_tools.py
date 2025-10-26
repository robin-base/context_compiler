from pathlib import Path

from context_compiler.tools import search_notes


def test_search_notes_by_title():
    """Test searching notes by title match."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("sarah", str(vault_path))

    assert len(results) > 0
    assert any(r["title"] == "Sarah" for r in results)
    assert all("path" in r for r in results)
    assert all("title" in r for r in results)
    assert all("tags" in r for r in results)
    assert all("modified" in r for r in results)
    assert all("match_type" in r for r in results)


def test_search_notes_by_content():
    """Test searching notes by content match."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("phoenix", str(vault_path))

    assert len(results) > 0
    assert any("Project Phoenix" in r["title"] for r in results)


def test_search_notes_empty_result():
    """Test search with no matches returns empty list."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("nonexistent xyz123", str(vault_path))

    assert results == []


def test_search_notes_invalid_vault():
    """Test error handling for invalid vault."""
    results = search_notes("test", "/nonexistent/path")

    assert "error" in results
