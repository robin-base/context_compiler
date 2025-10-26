---
name: context-compiler
description: Use when user wants to prep for meetings, calls, or work sessions - scans Obsidian vault for relevant context and generates focused brief
---

# Context Compiler

## When to Use This Skill

Use this skill when the user expresses intent to prepare for an upcoming activity:

**Trigger phrases:**
- "Prep me for [meeting/call/work session on X]"
- "What should I know before [meeting with X]?"
- "Brief me on [project/person/topic]"
- "Get me ready for [X]"
- "Context for [X]"

**Examples:**
- "Prep me for my meeting with Sarah"
- "What should I know before my 1-on-1 with my manager?"
- "Brief me on Project Phoenix"

## How to Use This Skill

1. **Extract the query** - Identify what they want to prep for
2. **Get vault path** - Ask user for Obsidian vault location if not configured
3. **Get vault name** - Extract vault name from path (needed for deep links)
4. **Run compilation** - Call ContextCompiler with query
5. **Display brief** - Show formatted markdown to user

## Implementation

```python
from pathlib import Path
from context_compiler import ContextCompiler

# Get vault path from user
vault_path = Path("/Users/robin/Documents/MyVault")
vault_name = vault_path.name  # "MyVault"

# Compile context
compiler = ContextCompiler(vault_path, vault_name)
brief = compiler.compile_context(query)

# Display to user
print(brief)
```

## Configuration

Ask user for vault path on first use, then remember for session.

## Error Handling

- **Vault not found:** Ask user to verify path
- **No matching notes:** Inform user, suggest different search terms
- **LLM failures:** Gracefully degrade (show notes without categorization/summary)
