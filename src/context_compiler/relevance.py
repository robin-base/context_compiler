from datetime import datetime
from pathlib import Path

from vault_explorer import SearchService, VaultService, extract_all_tags

from context_compiler.models import CandidateNote


class RelevanceEngine:
    """Finds relevant notes using hybrid search."""

    def __init__(self, vault_path: Path, max_candidates: int = 100) -> None:
        """Initialize engine for given vault.

        Args:
            vault_path: Path to Obsidian vault
            max_candidates: Maximum number of candidate notes to return
        """
        self.vault_path = Path(vault_path)
        self.max_candidates = max_candidates

        # Initialize vault services
        self.vault = VaultService(vault_path)
        # Load all notes to populate cache for search
        self.vault.get_all_notes()
        self.search = SearchService(self.vault)

    def _find_anchor_notes(self, query: str) -> list:
        """Find anchor notes via keyword search.

        Args:
            query: Search query

        Returns:
            List of Note objects matching query
        """
        # Search by title and content for full query
        title_matches = self.search.search_by_title(query)
        content_matches = self.search.search_content(query)

        # Also search for individual words
        words = query.lower().split()
        word_matches = []
        for word in words:
            # Skip common words
            if word in {'a', 'an', 'the', 'with', 'for', 'on', 'in', 'at', 'to', 'of'}:
                continue
            word_matches.extend(self.search.search_by_title(word))
            word_matches.extend(self.search.search_content(word))
            word_matches.extend(self.search.search_by_tag(word))

        # Combine and deduplicate
        all_matches = title_matches + content_matches + word_matches
        seen = set()
        unique_matches = []
        for note in all_matches:
            if note.path not in seen:
                seen.add(note.path)
                unique_matches.append(note)

        return unique_matches

    def find_relevant_notes(
        self,
        query: str,
        traversal_depth: int = 2,
    ) -> list[CandidateNote]:
        """Find all relevant notes for query.

        Args:
            query: Prep query (e.g., "meeting with Sarah")
            traversal_depth: How deep to traverse graph

        Returns:
            List of CandidateNote objects
        """
        # Step 1: Find anchor notes
        anchors = self._find_anchor_notes(query)

        if not anchors:
            return []

        # Step 2: Graph traversal from anchors
        connected = set()
        for anchor in anchors:
            connected.add(anchor.path)
            # Get connected notes
            linked_notes = self.vault.get_connected_notes(
                anchor,
                depth=traversal_depth,
                include_backlinks=True,
            )
            for note in linked_notes:
                connected.add(note.path)

        # Step 3: Convert to CandidateNote with metadata
        candidates = []
        for note_path in connected:
            if len(candidates) >= self.max_candidates:
                break

            # Load note if not in cache
            note = None
            for cached_note in self.vault._notes_cache.values():
                if cached_note.path == note_path:
                    note = cached_note
                    break

            if note is None:
                note = self.vault.load_note(note_path)

            # Extract metadata
            tags = extract_all_tags(note)
            category = note.frontmatter.get("type") or note.frontmatter.get("category")

            # Get snippet (first 200 chars or frontmatter summary)
            snippet = note.frontmatter.get("summary", "")
            if not snippet:
                snippet = note.content[:200].replace("\n", " ").strip()

            # Get modification time
            mtime = datetime.fromtimestamp(note_path.stat().st_mtime)

            candidate = CandidateNote(
                title=note.title,
                path=note.path,
                tags=tags,
                category=category,
                snippet=snippet,
                modified_time=mtime,
            )
            candidates.append(candidate)

        return candidates
