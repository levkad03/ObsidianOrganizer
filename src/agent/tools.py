from pathlib import Path

from langchain.tools import tool

from src.core.vault_manager import ObsidianVault

vault = ObsidianVault(Path("D:\Obsidian Notes\Test Vault"))


@tool
def list_notes_tool() -> list[str]:
    """List all note filenames in the Obsidian vault.

    Use this tool when the user wants to:
    - See what notes exist in the vault
    - Browse or explore the vault contents
    - Find a note by looking through available files
    - Get an overview of all notes and their locations

    Returns a list of relative file paths for all markdown (.md) files in the vault,
    including notes in subfolders (e.g., "Machine Learning/Neural Networks.md").
    """
    # Return relative paths for better readability
    return [str(p.relative_to(vault.path)) for p in vault.list_notes()]


@tool
def read_note_tool(name: str, folder: str | None = None) -> dict:
    """Read and retrieve the full content of a specific note from the vault.

    Use this tool when the user wants to:
    - See what's inside a specific note
    - Check the content of a note
    - Get information from a particular note
    - Review or examine a note's text and metadata

    ALWAYS use this tool before answering questions about a note's content.
    Never guess or make up note contents.

    Args:
        name: The note filename (with or without .md extension)
        folder: Optional folder path where the note is located (e.g., "Machine Learning")

    Returns a dictionary with:
    - "metadata": Parsed YAML frontmatter (tags, dates, etc.)
    - "content": The full text content of the note
    """
    full_name = f"{folder}/{name}" if folder else name
    return vault.read_note(full_name)


@tool
def build_index_tool() -> dict:
    """Build a comprehensive index of all notes in the vault with their metadata, links, and tags.

    Use this tool when the user wants to:
    - Understand the structure of the vault
    - Find notes by tags or links
    - See how notes are connected to each other
    - Get an overview of all metadata across notes
    - Analyze the vault organization

    Returns a dictionary mapping note names to their info:
    - "path": Relative file path
    - "metadata": YAML frontmatter data
    - "links": List of other notes this note links to (wikilinks)
    - "tags": List of tags used in the note
    """
    return vault.build_index()


@tool
def create_note_tool(
    name: str,
    metadata: dict | None = None,
    content: str | None = "",
    folder: str | None = None,
) -> str:
    """Create a new note in the Obsidian vault.

    Use this tool when the user wants to:
    - Create a new note
    - Add a new document to the vault
    - Start a new topic or page
    - Make a new file with specific content

    Will fail if a note with the same name already exists.
    Creates parent folders automatically if they don't exist.

    Args:
        name: The note filename (with or without .md extension)
        metadata: Optional YAML frontmatter as a dictionary (e.g., {"tags": ["ai", "ml"], "date": "2024-01-01"})
        content: The text content to write in the note body
        folder: Optional folder to create the note in (e.g., "Machine Learning" or "Projects/2024")
    """
    full_name = f"{folder}/{name}" if folder else name
    file_path = vault.create_note(full_name, metadata=metadata, content=content)
    return f"Created note: {file_path.relative_to(vault.path)}"


@tool
def replace_note_content_tool(
    name: str,
    content: str,
    metadata: dict | None = None,
    folder: str | None = None,
) -> str:
    """Replace the entire content of an existing note with new content.

    Use this tool when the user wants to:
    - Rewrite a note completely
    - Replace all content with new information
    - Update a note with entirely new text
    - Fix or correct a note by rewriting it

    This will DELETE all existing content and write the new content.
    Existing metadata will be preserved unless new metadata is provided.

    Args:
        name: The note filename (with or without .md extension)
        content: The new content that will replace everything in the note
        metadata: Optional new frontmatter metadata (merges with existing)
        folder: Optional folder path where the note is located (e.g., "Machine Learning")
    """
    full_name = f"{folder}/{name}" if folder else name
    vault.update_note(full_name, content=content, append=False, metadata=metadata)
    return f"Note '{full_name}' content has been completely replaced."


@tool
def append_to_note_tool(
    name: str,
    content: str,
    metadata: dict | None = None,
    folder: str | None = None,
) -> str:
    """Add content to the end of an existing note without removing existing content.

    Use this tool when the user wants to:
    - Add new information to a note
    - Append additional content
    - Add notes or comments to existing text
    - Extend a note with more details

    This will KEEP all existing content and add new content at the end.

    Args:
        name: The note filename (with or without .md extension)
        content: The content to add at the end of the note
        metadata: Optional frontmatter metadata to merge with existing
        folder: Optional folder path where the note is located (e.g., "Machine Learning")
    """
    full_name = f"{folder}/{name}" if folder else name
    vault.update_note(full_name, content=content, append=True, metadata=metadata)
    return f"Content appended to note '{full_name}' successfully."
