from pathlib import Path

from langchain.tools import tool

from src.core.vault_manager import ObsidianVault

vault = ObsidianVault(Path(r"D:\Obsidian Notes\Test Vault"))


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


@tool
def search_notes_tool(query: str) -> str:
    """Search for notes in the vault by keyword.

    Use this tool to find notes about a specific topic, search for content
    containing certain words, or look for notes with specific tags.

    Args:
        query: The keyword or phrase to search for
    """
    results = vault.search_notes(query)

    if not results:
        return f"No notes found matching '{query}'"

    # Format results as a string
    output = f"Found {len(results)} note(s) matching '{query}':\n\n"
    for r in results:
        output += f"- **{r['title']}** ({r['path']})\n"
        output += f"  Matched in: {', '.join(r['matched_in'])}\n"
        if r["snippet"]:
            output += f"  Snippet: {r['snippet']}\n"
        output += "\n"
    return output


@tool
def get_backlinks_tool(note_name: str) -> str:
    """Find all notes that link to a specific note (backlinks).

    Use this tool when the user wants to:
    - See what notes reference or link to a specific note
    - Find backlinks to a note
    - Understand how a note is connected in the vault
    - Discover which notes mention a particular topic

    Args:
        note_name: The name of the note to find backlinks for (without .md extension)
    """
    backlinks = vault.get_backlinks(note_name)

    if not backlinks:
        return f"No notes link to '{note_name}'"

    output = f"Found {len(backlinks)} note(s) linking to '{note_name}':\n\n"
    for name in backlinks:
        output += f"- {name}\n"
    return output


@tool
def find_orphaned_notes_tool() -> str:
    """Find notes that have no incoming or outgoing links (orphaned notes).

    Use this tool when the user wants to:
    - Find isolated or disconnected notes in the vault
    - Clean up notes that aren't linked to anything
    - Discover forgotten or abandoned notes
    - Analyze vault connectivity

    Orphaned notes are notes that neither link to other notes nor are linked by other notes.
    """
    orphans = vault.find_orphaned_notes()

    if not orphans:
        return "No orphaned notes found. All notes are connected!"

    output = f"Found {len(orphans)} orphaned note(s) with no links:\n\n"
    for name in orphans:
        output += f"- {name}\n"
    return output


@tool
def find_broken_links_tool() -> str:
    """Find wikilinks that point to notes that don't exist (broken links).

    Use this tool when the user wants to:
    - Find broken or invalid links in the vault
    - Identify notes that reference non-existent notes
    - Clean up the vault by fixing or removing broken links
    - Discover notes that need to be created

    Returns notes containing broken links and which links are broken.
    """
    broken = vault.find_broken_links()

    if not broken:
        return "No broken links found. All wikilinks point to existing notes!"

    total_broken = sum(len(links) for links in broken.values())
    output = f"Found {total_broken} broken link(s) in {len(broken)} note(s):\n\n"
    for note_name, missing_links in broken.items():
        output += f"**{note_name}** has broken links to:\n"
        for link in missing_links:
            output += f"  - [[{link}]]\n"
        output += "\n"
    return output


@tool
def suggest_connections_by_tags_tool() -> str:
    """Suggest potential connections between notes based on shared tags.

    Use this tool when the user wants to:
    - Find notes that might be related based on tags
    - Discover potential links between unconnected notes
    - Improve vault connectivity by finding tag-based relationships

    Returns pairs of notes that share tags but aren't currently linked.
    """

    suggestions = vault.suggest_connections_by_tags()

    if not suggestions:
        return "No tag-based connection suggestions found. Notes with shared tags are already linked!"

    output = (
        f"Found {len(suggestions)} potential connection(s) based on shared tags:\n\n"
    )

    for s in suggestions[:20]:  # Limit to top 20
        output += f"- **{s['note1']}** ↔ **{s['note2']}**\n"
        output += f"  Shared tags: {', '.join('#' + t for t in s['common_tags'])}\n\n"

    if len(suggestions) > 20:
        output += f"...and {len(suggestions) - 20} more suggestions.\n"

    return output


@tool
def suggest_connections_by_keywords_tool() -> str:
    """Suggest potential connections between notes based on shared keywords.

    Use this tool when the user wants to:
    - Find notes with similar content that aren't linked
    - Discover related notes based on word overlap
    - Find notes discussing similar topics

    Returns pairs of notes with significant keyword overlap that aren't currently linked.
    """

    suggestions = vault.suggest_connections_by_keywords()

    if not suggestions:
        return "No keyword-based connection suggestions found."

    output = f"Found {len(suggestions)} potential connection(s) based on keyword overlap:\n\n"
    for s in suggestions[:20]:
        output += f"- **{s['note1']}** ↔ **{s['note2']}**\n"
        output += (
            f"  Shared words ({s['shared_words']}): {', '.join(s['sample_words'])}\n\n"
        )

    if len(suggestions) > 20:
        output += f"...and {len(suggestions) - 20} more suggestions.\n"

    return output


@tool
def suggest_connections_by_graph_tool() -> str:
    """Suggest potential connections based on link patterns (friends of friends).

    Use this tool when the user wants to:
    - Find notes that are indirectly connected (via a common note)
    - Discover second-degree connections in the vault
    - Build a more tightly connected knowledge graph

    If note A links to B, and B links to C, suggests that A might want to link to C.
    """
    suggestions = vault.suggest_connections_by_graph()

    if not suggestions:
        return "No graph-based connection suggestions found."

    output = (
        f"Found {len(suggestions)} potential connection(s) based on link patterns:\n\n"
    )
    for s in suggestions[:20]:  # Limit to top 20
        output += f"- **{s['note1']}** → **{s['note2']}**\n"
        output += f"  Both connected via: [[{s['via']}]]\n\n"

    if len(suggestions) > 20:
        output += f"\n... and {len(suggestions) - 20} more suggestions."
    return output
