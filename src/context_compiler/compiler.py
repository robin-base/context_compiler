from pathlib import Path

from context_compiler.brief import BriefGenerator
from context_compiler.ranking import RankingService
from context_compiler.relevance import RelevanceEngine


class ContextCompiler:
    """Main orchestrator for context compilation."""

    def __init__(
        self,
        vault_path: Path,
        vault_name: str,
        max_candidates: int = 100,
        traversal_depth: int = 2,
    ) -> None:
        """Initialize context compiler.

        Args:
            vault_path: Path to Obsidian vault
            vault_name: Vault name for deep links
            max_candidates: Max candidates from relevance engine
            traversal_depth: Graph traversal depth
        """
        self.vault_path = Path(vault_path)
        self.vault_name = vault_name

        # Initialize services
        self.relevance_engine = RelevanceEngine(vault_path, max_candidates=max_candidates)
        self.ranking_service = RankingService()
        self.brief_generator = BriefGenerator(vault_name=vault_name)

        self.traversal_depth = traversal_depth

    def compile_context(self, query: str) -> str:
        """Compile context brief for query.

        Args:
            query: Prep query (e.g., "meeting with Sarah")

        Returns:
            Markdown formatted brief
        """
        # Step 1: Find relevant notes
        candidates = self.relevance_engine.find_relevant_notes(
            query,
            traversal_depth=self.traversal_depth,
        )

        if not candidates:
            return self.brief_generator.generate_brief([], [], query)

        # Step 2: Categorize with LLM
        very_relevant, potentially_relevant = self.ranking_service.categorize_notes(
            candidates,
            query,
        )

        # Step 3: Generate brief
        brief = self.brief_generator.generate_brief(
            very_relevant,
            potentially_relevant,
            query,
        )

        return brief
