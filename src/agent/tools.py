from pathlib import Path

from langchain.tools import tool

from src.core.vault_manager import ObsidianVault

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
    """Write new metadata and content to an existing note."""
    vault.write_note(name, metadata, content)
    return f"Note {name} updated successfuly."


@tool
def build_index_tool() -> dict:
    """Build an index of all notes (metadata, links, tags)."""
    return vault.build_index()


@tool
def create_note_tool(
    name: str, metadata: dict | None = None, content: str | None = ""
) -> str:
    """Create a new note with optional metadata and content."""
    file_path = vault.create_note(name, metadata=metadata, content=content)
    return f"Created note: {file_path.name}"


@tool
def update_note_tool(
    name: str,
    content: str | None = None,
    append: bool = True,
    metadata: dict | None = None,
) -> str:
    """Update an existing note: append/prepend content and merge metadata."""
    vault.update_note(name, content=content, append=append, metadata=metadata)
    return f"Note {name} updated successfully."
