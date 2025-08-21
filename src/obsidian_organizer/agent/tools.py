from pathlib import Path

from langchain.tools import tool

from obsidian_organizer.core.vault_manager import ObsidianVault

vault = ObsidianVault(Path("D:\Obsidian Notes\Test Vault"))


@tool
def list_notes_tool() -> list[str]:
    """List all note filenames in the vault."""
    return [str(p.name) for p in vault.list_notes()]


@tool
def read_note_tool(name: str) -> dict:
    """Read a note by name and return its metadata and content."""
    return vault.read_note(name)


@tool
def write_note_tool(name: str, metadata: dict, content: str) -> str:
    """Update an existing note with new metadata and content."""
    vault.write_note(name, metadata, content)
    return f"Note {name} updated successfuly."


@tool
def build_index_tool() -> dict:
    """Build an index of all notes (metadata, links, tags)."""
    return vault.build_index()
