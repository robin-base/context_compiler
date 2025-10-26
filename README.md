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
