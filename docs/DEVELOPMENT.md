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
