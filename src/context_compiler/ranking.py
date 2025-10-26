import re
from enum import Enum

from context_compiler.models import CandidateNote


class Relevance(Enum):
    """Relevance tier for notes."""
    VERY_RELEVANT = "VERY_RELEVANT"
    POTENTIALLY_RELEVANT = "POTENTIALLY_RELEVANT"
    NOT_RELEVANT = "NOT_RELEVANT"


class RankingService:
    """Filters notes using LLM categorization."""

    def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt. Override in tests.

        Args:
            prompt: Prompt to send to LLM

        Returns:
            LLM response text
        """
        # TODO: Implement actual LLM call
        # For now, this will be mocked in tests
        raise NotImplementedError("LLM integration not yet implemented")

    def _build_prompt(self, candidates: list[CandidateNote], query: str) -> str:
        """Build LLM prompt for categorization.

        Args:
            candidates: Notes to categorize
            query: Original prep query

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are helping prep for: {query}

Categorize each note as:
- VERY_RELEVANT: Recent interactions, open action items, critical context
- POTENTIALLY_RELEVANT: Related background, past decisions, context that might matter
- NOT_RELEVANT: Weak/tangential connection

Notes to categorize:
"""

        for i, candidate in enumerate(candidates, 1):
            tags_str = ", ".join(sorted(candidate.tags)) if candidate.tags else "none"
            prompt += f"""
{i}. Title: "{candidate.title}"
   Tags: {tags_str}
   Snippet: {candidate.snippet[:100]}
"""

        prompt += (
            "\nFor each note, respond with the number and categorization "
            "(e.g., '1. VERY_RELEVANT - reason')."
        )

        return prompt

    def _parse_response(
        self, response: str, candidates: list[CandidateNote]
    ) -> dict[int, Relevance]:
        """Parse LLM response into categorizations.

        Args:
            response: LLM response text
            candidates: Original candidates list

        Returns:
            Dict mapping candidate index to Relevance
        """
        categorizations = {}

        # Parse responses like "1. VERY_RELEVANT - reason"
        pattern = r'(\d+)\.\s*(VERY_RELEVANT|POTENTIALLY_RELEVANT|NOT_RELEVANT)'
        matches = re.findall(pattern, response)

        for match in matches:
            idx = int(match[0]) - 1  # Convert to 0-indexed
            relevance_str = match[1]

            if 0 <= idx < len(candidates):
                categorizations[idx] = Relevance(relevance_str)

        return categorizations

    def categorize_notes(
        self,
        candidates: list[CandidateNote],
        query: str,
    ) -> tuple[list[CandidateNote], list[CandidateNote]]:
        """Categorize notes into relevance tiers.

        Args:
            candidates: Notes to categorize
            query: Original prep query

        Returns:
            Tuple of (very_relevant, potentially_relevant) note lists
        """
        if not candidates:
            return [], []

        try:
            # Build prompt and call LLM
            prompt = self._build_prompt(candidates, query)
            response = self._call_llm(prompt)

            # Parse response
            categorizations = self._parse_response(response, candidates)

            # Group by relevance
            very_relevant = []
            potentially_relevant = []

            for i, candidate in enumerate(candidates):
                relevance = categorizations.get(i, Relevance.NOT_RELEVANT)

                if relevance == Relevance.VERY_RELEVANT:
                    very_relevant.append(candidate)
                elif relevance == Relevance.POTENTIALLY_RELEVANT:
                    potentially_relevant.append(candidate)

            # Sort by modified time (newest first) within each tier
            very_relevant.sort(key=lambda c: c.modified_time, reverse=True)
            potentially_relevant.sort(key=lambda c: c.modified_time, reverse=True)

            return very_relevant, potentially_relevant

        except Exception:
            # Fallback: treat all as potentially relevant
            sorted_candidates = sorted(candidates, key=lambda c: c.modified_time, reverse=True)
            return [], sorted_candidates
