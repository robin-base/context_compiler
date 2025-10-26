---
name: obsidian-prep
description: Prep for meetings, projects, and work sessions by gathering context from your Obsidian vault
---

# Obsidian Prep

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
