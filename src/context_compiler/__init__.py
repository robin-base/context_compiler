"""Context Compiler - Claude Code skill for Obsidian vault exploration."""

from context_compiler.tools import (
    get_linked_notes,
    get_note_metadata,
    list_notes,
    search_notes,
)

__version__ = "0.1.0"

__all__ = [
    "search_notes",
    "get_linked_notes",
    "list_notes",
    "get_note_metadata",
]
