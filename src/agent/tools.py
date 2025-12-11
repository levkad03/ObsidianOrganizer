from pathlib import Path

from langchain.tools import tool

from src.core.vault_manager import ObsidianVault

vault = ObsidianVault(Path("D:\Obsidian Notes\Test Vault"))


@tool
def list_notes_tool() -> list[str]:
    """List all note filenames in the vault."""
    # Return relative paths for better readability
    return [str(p.relative_to(vault.path)) for p in vault.list_notes()]


@tool
def read_note_tool(name: str, folder: str | None = None) -> dict:
    """Read a note by name and optional folder and return its metadata and content."""
    full_name = f"{folder}/{name}" if folder else name
    return vault.read_note(full_name)


@tool
def build_index_tool() -> dict:
    """Build an index of all notes (metadata, links, tags)."""
    return vault.build_index()


@tool
def create_note_tool(
    name: str,
    metadata: dict | None = None,
    content: str | None = "",
    folder: str | None = None,
) -> str:
    """Create a new note with optional metadata, content and folder."""
    full_name = f"{folder}/{name}" if folder else name
    file_path = vault.create_note(full_name, metadata=metadata, content=content)
    return f"Created note: {file_path.relative_to(vault.path)}"


@tool
def update_note_tool(
    name: str,
    content: str | None = None,
    append: bool = True,
    metadata: dict | None = None,
    folder: str | None = None,
) -> str:
    """Update an existing note: append/prepend content and merge metadata.
    Accepts optional folder."""
    full_name = f"{folder}/{name}" if folder else name
    vault.update_note(full_name, content=content, append=append, metadata=metadata)
    return f"Note {full_name} updated successfully."
