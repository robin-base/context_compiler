# Development Guide

## Setup

```bash
# Clone and install
git clone <repo>
cd context_compiler
uv sync --dev
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_relevance.py -v

# Single test
uv run pytest tests/test_relevance.py::test_find_anchor_notes -v

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
├── compiler.py       # Main orchestrator
├── relevance.py      # RelevanceEngine (search + traversal)
├── ranking.py        # RankingService (LLM categorization)
├── brief.py          # BriefGenerator (formatting)
├── models.py         # Data models
└── skill.py          # Claude Code entry point

tests/
├── test_relevance.py
├── test_ranking.py
├── test_brief.py
├── test_integration.py
└── fixtures/test_vault/  # Sample Obsidian vault
```

## Testing Strategy

- **Unit tests**: Mock external dependencies (vault I/O, LLM calls)
- **Integration tests**: Use test vault fixtures, mock LLM only
- **Fixtures**: `tests/fixtures/test_vault/` contains sample notes

## TODO: LLM Integration

Currently, LLM calls are stubbed with `NotImplementedError`. To integrate:

1. Choose LLM provider (Anthropic Claude, OpenAI, etc.)
2. Implement `RankingService._call_llm()`
3. Implement `BriefGenerator._generate_summary()`
4. Add provider credentials/config
5. Update tests to use real LLM (mark as slow/optional)

## Commit Conventions

Follow vault_explorer conventions:
- Describe change contents only
- No "Generated with Claude Code" signatures
- No Co-authored-by lines

Example:
```
Add graph traversal to RelevanceEngine

Implement BFS traversal with cycle detection.
```
