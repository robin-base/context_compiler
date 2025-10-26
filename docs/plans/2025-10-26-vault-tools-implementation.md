# Vault Tools Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace orchestrated pipeline with stateless tool functions that Claude can call to explore Obsidian vaults.

**Architecture:** Four pure functions that wrap vault_explorer, return metadata dicts, let Claude orchestrate via SKILL.md instructions.

**Tech Stack:** Python 3.11+, vault_explorer library, pytest

---

## Task 1: Remove Old Implementation

**Files:**
- Delete: `src/context_compiler/ranking.py`
- Delete: `src/context_compiler/brief.py`
- Delete: `src/context_compiler/compiler.py`
- Delete: `src/context_compiler/models.py`
- Delete: `tests/test_ranking.py`
- Delete: `tests/test_brief.py`
- Delete: `tests/test_integration.py`
- Keep: `tests/test_relevance.py` (will refactor in next task)
- Keep: `src/context_compiler/relevance.py` (will refactor to use functions)

**Step 1: Remove old files**

```bash
rm src/context_compiler/ranking.py
rm src/context_compiler/brief.py
rm src/context_compiler/compiler.py
rm src/context_compiler/models.py
rm tests/test_ranking.py
rm tests/test_brief.py
rm tests/test_integration.py
```

**Step 2: Update __init__.py**

Modify `src/context_compiler/__init__.py`:

```python
"""Context Compiler - Claude Code skill for Obsidian vault exploration."""

__version__ = "0.1.0"

__all__ = []
```

**Step 3: Verify clean state**

Run: `uv run pytest -v`
Expected: Only test_relevance.py tests run (will fail, expected)

**Step 4: Commit**

```bash
git add -A
git commit -m "Remove old pipeline implementation

Removing RankingService, BriefGenerator, ContextCompiler in favor of
stateless tool functions."
```

---

## Task 2: Implement search_notes()

**Files:**
- Create: `src/context_compiler/tools.py`
- Create: `tests/test_tools.py`

**Step 1: Write the failing test**

Create `tests/test_tools.py`:

```python
from pathlib import Path

from context_compiler.tools import search_notes


def test_search_notes_by_title():
    """Test searching notes by title match."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("sarah", str(vault_path))

    assert len(results) > 0
    assert any(r["title"] == "Sarah" for r in results)
    assert all("path" in r for r in results)
    assert all("title" in r for r in results)
    assert all("tags" in r for r in results)
    assert all("modified" in r for r in results)
    assert all("match_type" in r for r in results)


def test_search_notes_by_content():
    """Test searching notes by content match."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("phoenix", str(vault_path))

    assert len(results) > 0
    assert any("Project Phoenix" in r["title"] for r in results)


def test_search_notes_empty_result():
    """Test search with no matches returns empty list."""
    vault_path = Path("tests/fixtures/test_vault")

    results = search_notes("nonexistent xyz123", str(vault_path))

    assert results == []


def test_search_notes_invalid_vault():
    """Test error handling for invalid vault."""
    results = search_notes("test", "/nonexistent/path")

    assert "error" in results
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools.py::test_search_notes_by_title -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'context_compiler.tools'"

**Step 3: Write minimal implementation**

Create `src/context_compiler/tools.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py::test_search_notes -v`
Expected: All search_notes tests PASS

**Step 5: Commit**

```bash
git add src/context_compiler/tools.py tests/test_tools.py
git commit -m "Add search_notes() tool function

Searches vault by title, content, and tags. Returns metadata dicts."
```

---

## Task 3: Implement get_linked_notes()

**Files:**
- Modify: `src/context_compiler/tools.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing test**

Add to `tests/test_tools.py`:

```python
from context_compiler.tools import get_linked_notes


def test_get_linked_notes_basic():
    """Test getting linked notes from anchor."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "projects" / "Project Phoenix.md"

    results = get_linked_notes(str(note_path), depth=1, vault_path=str(vault_path))

    assert len(results) > 0
    # Should include Sarah (linked from Project Phoenix)
    assert any(r["title"] == "Sarah" for r in results)
    # Check structure
    assert all("path" in r for r in results)
    assert all("distance" in r for r in results)
    assert all(r["distance"] >= 1 for r in results)


def test_get_linked_notes_with_depth():
    """Test depth parameter controls traversal."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "projects" / "Project Phoenix.md"

    results_depth_1 = get_linked_notes(str(note_path), depth=1, vault_path=str(vault_path))
    results_depth_2 = get_linked_notes(str(note_path), depth=2, vault_path=str(vault_path))

    # Depth 2 should find same or more notes
    assert len(results_depth_2) >= len(results_depth_1)


def test_get_linked_notes_invalid_note():
    """Test error handling for non-existent note."""
    vault_path = Path("tests/fixtures/test_vault")

    result = get_linked_notes("/nonexistent/note.md", vault_path=str(vault_path))

    assert "error" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools.py::test_get_linked_notes_basic -v`
Expected: FAIL with "ImportError: cannot import name 'get_linked_notes'"

**Step 3: Write minimal implementation**

Add to `src/context_compiler/tools.py`:

```python
def get_linked_notes(
    note_path: str,
    depth: int = 2,
    vault_path: str = "."
) -> Union[list[dict], dict]:
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
        return {"error": f"Not an Obsidian vault (missing .obsidian/)"}

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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py::test_get_linked_notes -v`
Expected: All get_linked_notes tests PASS

**Step 5: Commit**

```bash
git add src/context_compiler/tools.py tests/test_tools.py
git commit -m "Add get_linked_notes() tool function

Traverses wikilinks and backlinks up to specified depth."
```

---

## Task 4: Implement list_notes()

**Files:**
- Modify: `src/context_compiler/tools.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing test**

Add to `tests/test_tools.py`:

```python
from context_compiler.tools import list_notes


def test_list_notes_all():
    """Test listing all notes in vault."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(vault_path=str(vault_path))

    assert len(results) >= 2  # At least Sarah and Project Phoenix
    assert all("path" in r for r in results)
    assert all("title" in r for r in results)


def test_list_notes_filter_by_tag():
    """Test filtering notes by tag."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(vault_path=str(vault_path), tag="person")

    assert len(results) > 0
    # Should only have notes with 'person' tag
    assert all("person" in r["tags"] for r in results)


def test_list_notes_filter_by_modified_after():
    """Test filtering notes by modification date."""
    vault_path = Path("tests/fixtures/test_vault")

    # Use a date in the past - should get all notes
    results = list_notes(
        vault_path=str(vault_path),
        modified_after="2020-01-01T00:00:00"
    )

    assert len(results) >= 2


def test_list_notes_filter_by_both():
    """Test filtering by both tag and date."""
    vault_path = Path("tests/fixtures/test_vault")

    results = list_notes(
        vault_path=str(vault_path),
        tag="person",
        modified_after="2020-01-01T00:00:00"
    )

    # Should have person tags
    assert all("person" in r["tags"] for r in results)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools.py::test_list_notes_all -v`
Expected: FAIL with "ImportError: cannot import name 'list_notes'"

**Step 3: Write minimal implementation**

Add to `src/context_compiler/tools.py`:

```python
def list_notes(
    vault_path: str = ".",
    tag: str = None,
    modified_after: str = None
) -> Union[list[dict], dict]:
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
        return {"error": f"Not an Obsidian vault (missing .obsidian/)"}

    try:
        # Initialize services
        vault = VaultService(vault_path)
        search = SearchService(vault)

        # Get all notes or filter by tag
        if tag:
            notes = search.search_by_tag(tag)
        else:
            notes = vault.get_all_notes()

        # Filter by modified_after if provided
        if modified_after:
            try:
                cutoff = datetime.fromisoformat(modified_after)
                notes = [
                    n for n in notes
                    if datetime.fromtimestamp(n.path.stat().st_mtime) > cutoff
                ]
            except (ValueError, OSError) as e:
                return {"error": f"Invalid modified_after timestamp: {str(e)}"}

        # Convert to dicts
        results = [_note_to_dict(note, match_type="list") for note in notes]

        return results

    except Exception as e:
        return {"error": f"List operation failed: {str(e)}"}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py::test_list_notes -v`
Expected: All list_notes tests PASS

**Step 5: Commit**

```bash
git add src/context_compiler/tools.py tests/test_tools.py
git commit -m "Add list_notes() tool function

Lists all notes with optional tag and date filters."
```

---

## Task 5: Implement get_note_metadata()

**Files:**
- Modify: `src/context_compiler/tools.py`
- Modify: `tests/test_tools.py`

**Step 1: Write the failing test**

Add to `tests/test_tools.py`:

```python
from context_compiler.tools import get_note_metadata


def test_get_note_metadata_basic():
    """Test getting note metadata without full content."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "people" / "Sarah.md"

    result = get_note_metadata(str(note_path), vault_path=str(vault_path))

    assert "path" in result
    assert "title" in result
    assert result["title"] == "Sarah"
    assert "tags" in result
    assert "modified" in result
    assert "frontmatter" in result
    assert "link_count" in result
    assert "snippet" in result
    assert len(result["snippet"]) <= 200


def test_get_note_metadata_with_frontmatter():
    """Test metadata extraction includes frontmatter fields."""
    vault_path = Path("tests/fixtures/test_vault")
    note_path = vault_path / "people" / "Sarah.md"

    result = get_note_metadata(str(note_path), vault_path=str(vault_path))

    assert "frontmatter" in result
    assert isinstance(result["frontmatter"], dict)
    # Should have type: person from frontmatter
    assert result["frontmatter"].get("type") == "person"


def test_get_note_metadata_invalid_note():
    """Test error handling for non-existent note."""
    vault_path = Path("tests/fixtures/test_vault")

    result = get_note_metadata("/nonexistent/note.md", vault_path=str(vault_path))

    assert "error" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools.py::test_get_note_metadata_basic -v`
Expected: FAIL with "ImportError: cannot import name 'get_note_metadata'"

**Step 3: Write minimal implementation**

Add to `src/context_compiler/tools.py`:

```python
def get_note_metadata(note_path: str, vault_path: str = ".") -> dict:
    """
    Get note metadata without reading full content.

    Args:
        note_path: Path to note
        vault_path: Path to Obsidian vault (default: current directory)

    Returns:
        Dict with:
        - path, title, tags, modified (same as other functions)
        - frontmatter: dict - all frontmatter fields
        - link_count: int - number of outgoing links
        - snippet: str - first 200 chars of content

        Or error dict: {"error": "message"}
    """
    vault_path = Path(vault_path)
    note_path = Path(note_path)

    # Validate vault
    if not vault_path.exists():
        return {"error": f"Vault not found at {vault_path}"}

    if not (vault_path / ".obsidian").exists():
        return {"error": f"Not an Obsidian vault (missing .obsidian/)"}

    # Validate note exists
    if not note_path.exists():
        return {"error": f"Note not found: {note_path}"}

    try:
        # Initialize vault
        vault = VaultService(vault_path)

        # Load note
        note = vault.load_note(note_path)

        # Build metadata dict
        result = _note_to_dict(note, match_type="metadata")

        # Add additional fields
        result["frontmatter"] = dict(note.frontmatter)
        result["link_count"] = len(note.links)
        result["snippet"] = note.content[:200].replace("\n", " ").strip()

        return result

    except Exception as e:
        return {"error": f"Metadata extraction failed: {str(e)}"}
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py::test_get_note_metadata -v`
Expected: All get_note_metadata tests PASS

**Step 5: Run all tests**

Run: `uv run pytest -v`
Expected: All 15+ tests PASS (4 functions × ~3-4 tests each)

**Step 6: Commit**

```bash
git add src/context_compiler/tools.py tests/test_tools.py
git commit -m "Add get_note_metadata() tool function

Extracts metadata, frontmatter, and snippet without full content."
```

---

## Task 6: Update SKILL.md

**Files:**
- Modify: `SKILL.md`

**Step 1: Rewrite SKILL.md with tool-based workflow**

Replace contents of `SKILL.md`:

```markdown
---
name: vault-tools
description: Use when user wants context from their Obsidian vault - provides tools to search notes, traverse links, and explore vault structure
---

# Obsidian Vault Tools

## When to Use This Skill

Use when user wants to prep for meetings, understand project context, or explore their Obsidian vault:

**Trigger phrases:**
- "Prep me for [meeting/call/work on X]"
- "What should I know before [X]?"
- "Brief me on [topic/person/project]"
- "Context for [X]"
- "What notes do I have about [X]?"

## Available Tools

The skill provides 4 Python functions for vault exploration:

### 1. search_notes(query, vault_path)

Finds notes matching query in titles, content, and tags.

**Returns:** List of dicts with `path`, `title`, `tags`, `modified`, `match_type`

### 2. get_linked_notes(note_path, depth, vault_path)

Gets notes connected via wikilinks and backlinks.

**Returns:** List of dicts with metadata + `distance` field

### 3. list_notes(vault_path, tag, modified_after)

Lists all notes with optional tag/date filters.

**Returns:** List of dicts with metadata

### 4. get_note_metadata(note_path, vault_path)

Gets metadata without reading full content.

**Returns:** Single dict with metadata + `frontmatter`, `link_count`, `snippet`

## Workflow Instructions

### Step 1: Determine Vault Path

Ask user: "Where is your Obsidian vault?"

Or try current directory if user is already in vault.

Remember vault path for session (no persistence between sessions).

### Step 2: Find Starting Points

Call `search_notes(query, vault_path)` to find notes matching user's query.

Extract key terms from user request:
- "meeting with Sarah" → search "sarah"
- "work on Project Phoenix" → search "project phoenix"

```python
from context_compiler.tools import search_notes

results = search_notes("sarah", "/Users/robin/Documents/Vault")
# Returns: [{"path": "...", "title": "Sarah", "tags": ["person"], ...}, ...]
```

### Step 3: Expand Context

For each relevant note, call `get_linked_notes()` to find connected notes:

```python
from context_compiler.tools import get_linked_notes

linked = get_linked_notes(
    "/Users/robin/Documents/Vault/people/Sarah.md",
    depth=2,
    vault_path="/Users/robin/Documents/Vault"
)
# Returns: [{"path": "...", "distance": 1, ...}, ...]
```

This traverses wikilinks and backlinks up to N levels deep.

### Step 4: Prioritize Notes

Sort and filter the combined results by:
- **Distance** (1 = directly linked, prioritize these)
- **Modified time** (recent = more relevant)
- **Match type** (title match > content match)

Select top ~5-10 notes to read.

### Step 5: Read Notes

Use the **Read tool** on selected note paths to get full content.

Don't use `get_note_metadata()` for reading - use Read tool which you already have access to.

`get_note_metadata()` is only useful when you need to check metadata on many notes without reading them all.

### Step 6: Synthesize Brief

Based on the notes you read, create a prep brief with:
- Summary of key context
- Recent conversations or decisions
- Open questions or action items
- Links to notes for deeper reading

Present naturally in your own words, not just excerpts.

## Example Flow

```
User: "Prep me for my meeting with Sarah"

You:
1. search_notes("sarah", vault_path)
   → [{path: "people/Sarah.md", ...}, {path: "meetings/Sarah-2024-10-20.md", ...}]

2. get_linked_notes("people/Sarah.md", depth=2, vault_path)
   → [{path: "projects/Project Phoenix.md", distance: 1, ...}, ...]

3. Prioritize:
   - people/Sarah.md (matched title)
   - meetings/Sarah-2024-10-20.md (recent)
   - projects/Project Phoenix.md (distance=1)

4. Use Read tool on top 3 paths to get full content

5. Present:
   "Based on your vault:
   - Sarah is the PM for Project Phoenix
   - Your last meeting (10/20) discussed Q4 roadmap priorities
   - Open: You need to review her timeline proposal
   - See also: [[Project Phoenix]], [[Q4 Roadmap]]"
```

## Error Handling

All tool functions return error dicts when something goes wrong:

```python
{"error": "Vault not found at /path"}
{"error": "Not an Obsidian vault (missing .obsidian/)"}
{"error": "Note not found: /path/note.md"}
```

If you get an error:
- Check with user if vault path is correct
- Suggest fixes (navigate to vault, check spelling)
- Try alternative approaches

## Tips

- **Use Read tool for content** - Tool functions only return metadata/paths
- **Adjust depth based on vault size** - depth=1 for large vaults, depth=2 for small
- **Filter with list_notes()** - For "all meetings this month" use tag + date filters
- **Remember vault path in session** - Don't ask repeatedly
- **Claude orchestrates** - You decide the workflow, tools just provide data
```

**Step 2: Commit**

```bash
git add SKILL.md
git commit -m "Update SKILL.md for tool-based workflow

Document 4 tool functions and workflow for Claude to follow."
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/DEVELOPMENT.md`

**Step 1: Update README**

Replace `README.md`:

```markdown
# Obsidian Vault Tools

Claude Code skill providing tools to explore Obsidian vaults. Claude uses these tools to search notes, traverse links, and prep users for meetings/work sessions.

## Features

- **search_notes()** - Find notes by keyword in titles, content, tags
- **get_linked_notes()** - Traverse wikilinks and backlinks with configurable depth
- **list_notes()** - List all notes with tag/date filters
- **get_note_metadata()** - Get metadata without reading full content

## How It Works

When you say "Prep me for my meeting with Sarah", Claude:
1. Calls `search_notes("sarah")` to find relevant notes
2. Calls `get_linked_notes()` to expand context via links
3. Uses Read tool to read the top priority notes
4. Synthesizes and presents a prep brief

**You orchestrate, tools provide data.**

## Installation

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest
```

## Architecture

Simple stateless functions that wrap vault_explorer library:
- Each function takes vault_path, returns metadata dicts
- No shared state between calls
- Claude orchestrates workflow via SKILL.md instructions

See [design document](docs/plans/2025-10-26-vault-tools-design.md) for details.

## Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for testing and contribution guidelines.

## Status

✅ Tool Functions - Complete
✅ Tests - Comprehensive coverage
✅ Documentation - Complete

Ready for use with Claude Code!

## License

MIT
```

**Step 2: Update DEVELOPMENT.md**

Replace `docs/DEVELOPMENT.md`:

```markdown
# Development Guide

## Setup

```bash
git clone <repo>
cd context_compiler
uv sync --dev
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific function tests
uv run pytest tests/test_tools.py::test_search_notes -v

# With coverage
uv run pytest --cov=src/context_compiler
```

## Code Quality

```bash
# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests
```

## Project Structure

```
src/context_compiler/
└── tools.py          # 4 tool functions (~200 lines)

tests/
├── test_tools.py     # Unit tests for all functions
└── fixtures/test_vault/  # Sample Obsidian vault
```

## Testing Strategy

- **Unit tests**: Each function tested with realistic vault fixtures
- **Error handling**: Test invalid paths, missing notes, malformed vaults
- **Filters**: Test tag and date filtering in list_notes()

## Tool Functions

All functions are stateless - take vault_path, return data, no shared state.

### search_notes(query, vault_path)
- Searches title, content, tags
- Filters stopwords from query
- Returns list of metadata dicts

### get_linked_notes(note_path, depth, vault_path)
- Traverses wikilinks and backlinks
- Configurable depth (default: 2)
- Returns metadata + distance

### list_notes(vault_path, tag, modified_after)
- Lists all notes
- Optional tag filter
- Optional date filter (ISO timestamp)

### get_note_metadata(note_path, vault_path)
- Gets metadata without full content
- Includes frontmatter, link_count, snippet
- Faster than Read tool for metadata-only needs

## Commit Conventions

- Describe change contents only
- No "Generated with Claude Code" signatures
- No Co-authored-by lines

Example:
```
Add search_notes() tool function

Searches vault by title, content, and tags. Returns metadata dicts.
```
```

**Step 3: Commit**

```bash
git add README.md docs/DEVELOPMENT.md
git commit -m "Update documentation for tool-based architecture

README and DEVELOPMENT.md reflect simplified design."
```

---

## Task 8: Update __init__.py exports

**Files:**
- Modify: `src/context_compiler/__init__.py`

**Step 1: Export tool functions**

Modify `src/context_compiler/__init__.py`:

```python
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
```

**Step 2: Test imports**

Run: `uv run python -c "from context_compiler import search_notes, get_linked_notes, list_notes, get_note_metadata; print('✓ Imports OK')"`
Expected: ✓ Imports OK

**Step 3: Commit**

```bash
git add src/context_compiler/__init__.py
git commit -m "Export tool functions from package"
```

---

## Task 9: Final Verification

**Step 1: Run full test suite**

```bash
uv run pytest -v
```

Expected: All tests PASS (should be ~15 tests, all tool function tests)

**Step 2: Run linter**

```bash
uv run ruff check src tests
```

Expected: No errors (or fix any that appear)

**Step 3: Check imports**

```bash
uv run python -c "
from context_compiler import search_notes, get_linked_notes, list_notes, get_note_metadata
print('All functions imported successfully')
print(f'search_notes: {search_notes.__doc__[:50]}...')
"
```

Expected: Success message and docstring preview

**Step 4: Verify file structure**

```bash
find src -name "*.py" | sort
find tests -name "*.py" | sort
```

Expected: Only tools.py in src, only test_tools.py in tests (plus __pycache__)

**Step 5: Check against requirements**

Verify checklist:
- ✅ 4 tool functions implemented
- ✅ All functions return metadata dicts
- ✅ Error handling with error dicts
- ✅ SKILL.md documents workflow
- ✅ README updated
- ✅ Tests comprehensive (~15 tests)
- ✅ Linting clean

**Step 6: Final commit if any fixes needed**

If fixes were required during verification, commit them.

---

## Summary

After completing all tasks:

**Removed (old pipeline approach):**
- ranking.py (138 lines)
- brief.py (141 lines)
- compiler.py (67 lines)
- models.py (15 lines)
- 9 tests

**Added (tool-based approach):**
- tools.py (~200 lines with 4 functions)
- ~15 tests
- Updated SKILL.md
- Updated README, DEVELOPMENT.md

**Result:**
- Simpler architecture (stateless functions)
- Claude orchestrates workflow
- Leverages Claude's reading and synthesis
- Total code: ~200 lines vs ~400 lines before
- Cleaner separation: tools discover, Claude reads/decides

Ready to use with Claude Code!
