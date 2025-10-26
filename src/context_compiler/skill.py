"""Claude Code skill entry point."""

from pathlib import Path

from context_compiler import ContextCompiler


def run_skill(query: str, vault_path: str) -> str:
    """Run context compiler skill.

    Args:
        query: Prep query from user
        vault_path: Path to Obsidian vault

    Returns:
        Markdown formatted brief
    """
    vault_path = Path(vault_path)

    # Validate vault exists
    if not vault_path.exists():
        return f"Error: Vault not found at {vault_path}"

    if not (vault_path / ".obsidian").exists():
        return f"Error: {vault_path} does not appear to be an Obsidian vault (missing .obsidian/)"

    # Extract vault name
    vault_name = vault_path.name

    # Compile context
    compiler = ContextCompiler(vault_path, vault_name)
    brief = compiler.compile_context(query)

    return brief
