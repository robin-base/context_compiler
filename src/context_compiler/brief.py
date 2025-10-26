from datetime import datetime
from urllib.parse import quote

from context_compiler.models import CandidateNote


class BriefGenerator:
    """Creates formatted markdown briefs."""

    def __init__(self, vault_name: str) -> None:
        """Initialize generator.

        Args:
            vault_name: Name of Obsidian vault (for deep links)
        """
        self.vault_name = vault_name

    def _generate_summary(
        self,
        very_relevant: list[CandidateNote],
        potentially_relevant: list[CandidateNote],
        query: str,
    ) -> str:
        """Generate LLM summary of notes.

        Args:
            very_relevant: Very relevant notes
            potentially_relevant: Potentially relevant notes
            query: Original query

        Returns:
            2-3 sentence summary
        """
        # TODO: Implement actual LLM call
        # For now, this will be mocked in tests
        raise NotImplementedError("LLM integration not yet implemented")

    def _format_relative_time(self, dt: datetime) -> str:
        """Format datetime as relative time string.

        Args:
            dt: Datetime to format

        Returns:
            Relative time string (e.g., "2 days ago")
        """
        now = datetime.now()
        delta = now - dt

        if delta.days == 0:
            return "today"
        elif delta.days == 1:
            return "yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.days < 365:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"

    def _format_note_entry(self, note: CandidateNote) -> str:
        """Format a single note as markdown entry.

        Args:
            note: Note to format

        Returns:
            Formatted markdown string
        """
        # Title
        entry = f"### {note.title}\n\n"

        # Metadata line
        tags_str = ", ".join(sorted(note.tags)) if note.tags else "none"
        time_str = self._format_relative_time(note.modified_time)
        entry += f"*Tags: {tags_str} | Modified: {time_str}*\n\n"

        # Snippet
        entry += f"{note.snippet}\n\n"

        # Obsidian link
        encoded_path = quote(str(note.path))
        obsidian_url = f"obsidian://open?vault={self.vault_name}&file={encoded_path}"
        entry += f"[Open in Obsidian]({obsidian_url})\n\n"

        return entry

    def generate_brief(
        self,
        very_relevant: list[CandidateNote],
        potentially_relevant: list[CandidateNote],
        query: str,
    ) -> str:
        """Generate complete markdown brief.

        Args:
            very_relevant: Very relevant notes
            potentially_relevant: Potentially relevant notes
            query: Original prep query

        Returns:
            Formatted markdown brief
        """
        brief = f"# Prep for {query}\n\n"

        # Generate summary (with LLM)
        try:
            summary = self._generate_summary(very_relevant, potentially_relevant, query)
            brief += f"## Summary\n\n{summary}\n\n"
        except NotImplementedError:
            # Skip summary if LLM not implemented yet
            pass
        except Exception:
            # Skip summary on LLM failure
            pass

        # Very Relevant section
        if very_relevant:
            brief += "## Very Relevant\n\n"
            for note in very_relevant:
                brief += self._format_note_entry(note)

        # Potentially Relevant section
        if potentially_relevant:
            brief += "## Potentially Relevant\n\n"
            for note in potentially_relevant:
                brief += self._format_note_entry(note)

        # Handle empty case
        if not very_relevant and not potentially_relevant:
            brief += (
                f"No notes found related to '{query}'. "
                f"Try a different search term or check your vault.\n"
            )

        return brief
