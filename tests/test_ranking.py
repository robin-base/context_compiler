from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from context_compiler.models import CandidateNote
from context_compiler.ranking import RankingService


def test_ranking_service_init():
    """Test initializing RankingService."""
    service = RankingService()
    assert service is not None


def test_categorize_notes_with_mock_llm():
    """Test categorizing notes using mocked LLM."""
    service = RankingService()

    candidates = [
        CandidateNote(
            title="Meeting with Sarah - 2024-10-20",
            path=Path("sarah-meeting.md"),
            tags={"meeting", "sarah"},
            category="meeting",
            snippet="Discussed Q4 roadmap",
            modified_time=datetime.now(),
        ),
        CandidateNote(
            title="Old Note",
            path=Path("old.md"),
            tags=set(),
            category=None,
            snippet="Unrelated content",
            modified_time=datetime(2020, 1, 1),
        ),
    ]

    # Mock LLM to return categorization
    mock_response = """
    1. VERY_RELEVANT - Recent meeting, directly about Sarah
    2. NOT_RELEVANT - Old and unrelated
    """

    with patch.object(service, '_call_llm', return_value=mock_response):
        very_rel, pot_rel = service.categorize_notes(candidates, "meeting with Sarah")

    # Should categorize correctly
    assert len(very_rel) == 1
    assert very_rel[0].title == "Meeting with Sarah - 2024-10-20"
    assert len(pot_rel) == 0


def test_categorize_notes_fallback_on_llm_failure():
    """Test fallback when LLM fails."""
    service = RankingService()

    candidates = [
        CandidateNote(
            title="Test",
            path=Path("test.md"),
            tags=set(),
            category=None,
            snippet="Test",
            modified_time=datetime.now(),
        ),
    ]

    # Mock LLM to raise exception
    with patch.object(service, '_call_llm', side_effect=Exception("API Error")):
        very_rel, pot_rel = service.categorize_notes(candidates, "test query")

    # Should fall back to treating all as potentially relevant
    assert len(very_rel) == 0
    assert len(pot_rel) == 1
