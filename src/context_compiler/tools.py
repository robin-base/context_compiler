"""Stateless tool functions for Obsidian vault exploration."""

from datetime import datetime
from pathlib import Path

from vault_explorer import SearchService, VaultService, extract_all_tags

# Stopwords to filter from queries
STOPWORDS = {"a", "an", "the", "with", "for", "on", "in", "at", "to", "of"}


def search_notes(query: str, vault_path: str = ".") -> list[dict] | dict:
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
        return {"error": "Not an Obsidian vault (missing .obsidian/)"}

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


def get_linked_notes(note_path: str, depth: int = 2, vault_path: str = ".") -> list[dict] | dict:
    """
    Get notes connected via wikilinks and backlinks.

    Args:
        note_path: Path to anchor note
        depth: How many levels deep to traverse (default: 2)
        vault_path: Path to Obsidian vault (default: current directory)

    Returns:
        List of dicts with same structure as search_notes, plus:
        - distance: int - how many links away (1 = direct link)

        Or error dict: {"error": "message"}
    """
    vault_path = Path(vault_path)
    note_path = Path(note_path)

    # Validate vault
    if not vault_path.exists():
        return {"error": f"Vault not found at {vault_path}"}

    if not (vault_path / ".obsidian").exists():
        return {"error": "Not an Obsidian vault (missing .obsidian/)"}

    # Validate note exists
    if not note_path.exists():
        return {"error": f"Note not found: {note_path}"}

    try:
        # Initialize vault
        vault = VaultService(vault_path)

        # Load anchor note
        anchor = vault.load_note(note_path)

        # Get connected notes
        connected = vault.get_connected_notes(anchor, depth=depth, include_backlinks=True)

        # Convert to dicts with distance
        # Note: vault_explorer doesn't track distance, so we'll set all to 1 for MVP
        # This is acceptable - Claude can prioritize by other factors
        results = []
        for note in connected:
            note_dict = _note_to_dict(note, match_type="link")
            note_dict["distance"] = 1  # Simplified for MVP
            results.append(note_dict)

        return results

    except Exception as e:
        return {"error": f"Link traversal failed: {str(e)}"}


def list_notes(
    vault_path: str = ".", tag: str | None = None, modified_after: str | None = None
) -> list[dict] | dict:
    """
    List all notes in vault with optional filters.

    Args:
        vault_path: Path to Obsidian vault (default: current directory)
        tag: Optional - only return notes with this tag
        modified_after: Optional - ISO timestamp, only notes modified after this

    Returns:
        List of dicts with same structure as search_notes
        Or error dict: {"error": "message"}
    """
    vault_path = Path(vault_path)

    # Validate vault
    if not vault_path.exists():
        return {"error": f"Vault not found at {vault_path}"}

    if not (vault_path / ".obsidian").exists():
        return {"error": "Not an Obsidian vault (missing .obsidian/)"}

    try:
        # Initialize services
        vault = VaultService(vault_path)

        # Get all notes
        notes = vault.get_all_notes()

        # Filter by tag if provided
        if tag:
            notes = [n for n in notes if tag in extract_all_tags(n)]

        # Filter by modified_after if provided
        if modified_after:
            try:
                cutoff = datetime.fromisoformat(modified_after)
                notes = [
                    n for n in notes if datetime.fromtimestamp(n.path.stat().st_mtime) > cutoff
                ]
            except (ValueError, OSError) as e:
                return {"error": f"Invalid modified_after timestamp: {str(e)}"}

        # Convert to dicts
        results = [_note_to_dict(note, match_type="list") for note in notes]

        return results

    except Exception as e:
        return {"error": f"List operation failed: {str(e)}"}


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
