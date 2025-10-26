from pathlib import Path

from context_compiler.models import CandidateNote
from context_compiler.relevance import RelevanceEngine


def test_relevance_engine_init():
    """Test initializing RelevanceEngine with vault path."""
    vault_path = Path("tests/fixtures/test_vault")
    engine = RelevanceEngine(vault_path)

    assert engine.vault_path == vault_path
    assert engine.vault is not None


def test_find_anchor_notes():
    """Test finding anchor notes via keyword search."""
    vault_path = Path("tests/fixtures/test_vault")
    engine = RelevanceEngine(vault_path)

    # Search for "sarah"
    anchors = engine._find_anchor_notes("sarah")

    # Should find Sarah note
    assert len(anchors) > 0
    titles = [note.title for note in anchors]
    assert "Sarah" in titles


def test_find_relevant_notes_basic():
    """Test basic relevance finding."""
    vault_path = Path("tests/fixtures/test_vault")
    engine = RelevanceEngine(vault_path)

    # Search for meeting with Sarah
    candidates = engine.find_relevant_notes("meeting with sarah")

    # Should return CandidateNote objects
    assert len(candidates) > 0
    assert all(isinstance(c, CandidateNote) for c in candidates)

    # Should include Sarah and related notes
    titles = {c.title for c in candidates}
    assert "Sarah" in titles
