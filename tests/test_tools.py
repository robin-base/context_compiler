from pathlib import Path

from context_compiler.tools import get_linked_notes, list_notes, search_notes


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


def test_get_linked_notes_basic():
    """Test getting linked notes from anchor."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "projects" / "Project Phoenix.md"

    results = get_linked_notes(str(note_path), depth=1, vault_path=str(vault_path))

    assert len(results) > 0
    # Should include Sarah (linked from Project Phoenix)
    assert any(r["title"] == "Sarah" for r in results)
    # Check structure
    assert all("path" in r for r in results)
    assert all("distance" in r for r in results)
    assert all(r["distance"] >= 1 for r in results)


def test_get_linked_notes_with_depth():
    """Test depth parameter controls traversal."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "projects" / "Project Phoenix.md"

    results_depth_1 = get_linked_notes(str(note_path), depth=1, vault_path=str(vault_path))
    results_depth_2 = get_linked_notes(str(note_path), depth=2, vault_path=str(vault_path))

    # Depth 2 should find same or more notes
    assert len(results_depth_2) >= len(results_depth_1)


def test_get_linked_notes_invalid_note():
    """Test error handling for non-existent note."""
    vault_path = Path("tests/fixtures/test_vault")

    result = get_linked_notes("/nonexistent/note.md", vault_path=str(vault_path))

    assert "error" in result


def test_list_notes_all():
    """Test listing all notes in vault."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(vault_path=str(vault_path))

    assert len(results) >= 2  # At least Sarah and Project Phoenix
    assert all("path" in r for r in results)
    assert all("title" in r for r in results)


def test_list_notes_filter_by_tag():
    """Test filtering notes by tag."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(vault_path=str(vault_path), tag="person")

    assert len(results) > 0
    # Should only have notes with 'person' tag
    assert all("person" in r["tags"] for r in results)


def test_list_notes_filter_by_modified_after():
    """Test filtering notes by modification date."""
    vault_path = Path("tests/fixtures/test_vault")

    # Use a date in the past - should get all notes
    results = list_notes(vault_path=str(vault_path), modified_after="2020-01-01T00:00:00")

    assert len(results) >= 2


def test_list_notes_filter_by_both():
    """Test filtering by both tag and date."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(
        vault_path=str(vault_path), tag="person", modified_after="2020-01-01T00:00:00"
    )

    # Should have person tags
    assert all("person" in r["tags"] for r in results)
