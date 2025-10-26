"""Stateless tool functions for Obsidian vault exploration."""

from datetime import datetime
from pathlib import Path
from typing import Union

from vault_explorer import SearchService, VaultService, extract_all_tags


# Stopwords to filter from queries
STOPWORDS = {"a", "an", "the", "with", "for", "on", "in", "at", "to", "of"}


def search_notes(query: str, vault_path: str = ".") -> Union[list[dict], dict]:
    """
    Find notes matching query in titles, content, and tags.

    Args:
        query: Search string
        vault_path: Path to Obsidian vault (default: current directory)

    Returns:
        List of dicts with:
        - path: str - absolute path to note
        - title: str - note title (filename without .md)
        - tags: list[str] - tags from frontmatter + content
        - modified: str - ISO timestamp
        - match_type: str - "title" | "content" | "tag"

        Or error dict: {"error": "message"}
    """
    vault_path = Path(vault_path)

    # Validate vault
    if not vault_path.exists():
        return {"error": f"Vault not found at {vault_path}"}

    if not (vault_path / ".obsidian").exists():
        return {"error": f"Not an Obsidian vault (missing .obsidian/)"}

    try:
        # Initialize services
        vault = VaultService(vault_path)
        vault.get_all_notes()  # Populate cache
        search = SearchService(vault)

        # Parse query
        query_lower = query.lower()
        words = [w for w in query_lower.split() if w not in STOPWORDS]

        # Search
        results = []
        seen = set()

        # Search by title (full query and individual words)
        for term in [query] + words:
            for note in search.search_by_title(term):
                if note.path not in seen:
                    seen.add(note.path)
                    results.append(_note_to_dict(note, "title"))

        # Search by content
        for term in [query] + words:
            for note in search.search_content(term):
                if note.path not in seen:
                    seen.add(note.path)
                    results.append(_note_to_dict(note, "content"))

        # Search by tag
        for word in words:
            for note in search.search_by_tag(word):
                if note.path not in seen:
                    seen.add(note.path)
                    results.append(_note_to_dict(note, "tag"))

        return results

    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def _note_to_dict(note, match_type: str = "unknown") -> dict:
    """Convert Note object to dict with metadata."""
    tags = extract_all_tags(note)

    try:
        mtime = datetime.fromtimestamp(note.path.stat().st_mtime)
        modified = mtime.isoformat()
    except (FileNotFoundError, OSError):
        modified = datetime.now().isoformat()

    return {
        "path": str(note.path),
        "title": note.title,
        "tags": list(tags),
        "modified": modified,
        "match_type": match_type,
    }
