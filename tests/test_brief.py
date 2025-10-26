from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from context_compiler.brief import BriefGenerator
from context_compiler.models import CandidateNote


def test_brief_generator_init():
    """Test initializing BriefGenerator."""
    generator = BriefGenerator(vault_name="TestVault")
    assert generator.vault_name == "TestVault"


def test_format_note_entry():
    """Test formatting a single note entry."""
    generator = BriefGenerator(vault_name="TestVault")

    note = CandidateNote(
        title="Meeting with Sarah",
        path=Path("people/sarah-meeting.md"),
        tags={"meeting", "sarah"},
        category="meeting",
        snippet="Discussed Q4 roadmap and priorities",
        modified_time=datetime(2024, 10, 20, 14, 30),
    )

    entry = generator._format_note_entry(note)

    assert "### Meeting with Sarah" in entry
    assert "meeting, sarah" in entry.lower()
    assert "Discussed Q4 roadmap" in entry
    assert "obsidian://open" in entry


def test_generate_brief_with_mock_llm():
    """Test generating full brief with mocked LLM."""
    generator = BriefGenerator(vault_name="TestVault")

    very_relevant = [
        CandidateNote(
            title="Recent Meeting",
            path=Path("meeting.md"),
            tags={"meeting"},
            category="meeting",
            snippet="Important discussion",
            modified_time=datetime.now(),
        ),
    ]

    potentially_relevant = [
        CandidateNote(
            title="Background Info",
            path=Path("background.md"),
            tags={"info"},
            category=None,
            snippet="Related context",
            modified_time=datetime(2024, 10, 1),
        ),
    ]

    mock_summary = "You have one recent meeting and relevant background info."

    with patch.object(generator, '_generate_summary', return_value=mock_summary):
        brief = generator.generate_brief(
            very_relevant,
            potentially_relevant,
            query="meeting prep",
        )

    assert "# Prep for meeting prep" in brief
    assert "## Summary" in brief
    assert mock_summary in brief
    assert "## Very Relevant" in brief
    assert "## Potentially Relevant" in brief
    assert "Recent Meeting" in brief
    assert "Background Info" in brief
