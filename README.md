# Context Compiler

A Claude Code skill that prepares you for meetings, calls, and work sessions by scanning your Obsidian vault for relevant context.

## Features

- **Hybrid Search**: Keyword matching → graph traversal → LLM filtering
- **Smart Briefs**: LLM-generated summaries with categorized sections
- **Deep Links**: Click to open notes directly in Obsidian
- **Fast**: Typical compilation in 3-10 seconds

## Usage

When using Claude Code, simply ask:

```
Prep me for my meeting with Sarah
```

Claude will automatically invoke this skill, scan your Obsidian vault, and provide a focused brief with:
- Executive summary
- Very relevant notes (recent conversations, action items)
- Potentially relevant notes (background, context)

## Installation

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest
```

## Architecture

Three-layer service architecture:

1. **RelevanceEngine** - Finds notes via hybrid search
2. **RankingService** - Categorizes with LLM (VERY/POTENTIALLY/NOT relevant)
3. **BriefGenerator** - Creates formatted markdown output

See [design document](docs/plans/2025-10-26-context-compiler-mvp.md) for details.

## Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for contribution guidelines.

## Status

✅ MVP Complete - Basic functionality working
🚧 LLM Integration - TODO: Connect to actual LLM API

## License

MIT
