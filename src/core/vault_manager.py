from pathlib import Path
from typing import Any

import yaml

from src.core.utils import (
    extract_tags,
    extract_wikilinks,
    parse_frontmatter,
    safe_write,
)


class ObsidianVault:
    """
    A manager for interacting with an Obsidian vault.

    Provides utilities for listing, reading, writing, and indexing notes
    within an Obsidian vault. Enforces safe path handling to prevent
    access outside of the vault directory.
    """

    def __init__(self, path: Path) -> None:
        """
        Initialize the vault manager.

        Args:
            path (Path): Path to the root of the Obsidian vault.

        Raises:
            ValueError: If the given path does not contain a `.obsidian` folder.
        """
        self.path = path

        if not (self.path / ".obsidian").exists():
            raise ValueError("Not a valid obsidian vault")

    def list_notes(self) -> list[Path]:
        """
        List all markdown notes in the vault.

        Returns:
            list[Path]: A list of paths to all `.md` files within the vault.
        """
        return list(self.path.glob("**/*.md"))

    def _resolve_path(self, name: str) -> Path:
        """
        Resolve a note name into a safe absolute path inside the vault.

        Ensures that the resolved path is inside the vault directory.

        Args:
            name (str): The name of the note (with or without `.md` extension).

        Returns:
            Path: The resolved absolute path to the note file.

        Raises:
            ValueError: If the resolved path is outside the vault root.
        """
        if not name.endswith(".md"):
            name += ".md"

        file_path = (self.path / name).resolve()

        if not str(file_path).startswith(str(self.path.resolve())):
            raise ValueError("Attempted access outside of vault")

        return file_path

    def read_note(self, name: str) -> dict[str, Any]:
        """
        Read a note from the vault and parse its frontmatter.

        Args:
            name (str): The name of the note to read.

        Returns:
            dict: A dictionary with:
                - "metadata": (dict) Parsed YAML frontmatter (if any).
                - "content": (str) Note body without frontmatter.

        Raises:
            FileNotFoundError: If the note does not exist in the vault.
        """
        file_path = self._resolve_path(name)
        if not file_path.exists():
            raise FileNotFoundError(f"Note '{name}' not found in vault")
        text = file_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        return {"metadata": meta, "content": body}

    def write_note(self, name: str, metadata: dict, content: str) -> None:
        """
        Safely write content and metadata to an existing note.

        Overwrites the note content after prepending YAML frontmatter.
        Uses atomic writes to avoid file corruption.

        Args:
            name (str): The name of the note to update.
            metadata (dict): Metadata to include as YAML frontmatter.
            content (str): Body text of the note.

        Raises:
            FileNotFoundError: If the note does not exist in the vault.
        """
        yaml_block = f"---\n{yaml.safe_dump(metadata)}---\n\n" if metadata else ""
        file_path = self._resolve_path(name)
        if not file_path.exists():
            raise FileNotFoundError(f"Note '{name}' not found in vault")

        safe_write(file_path, yaml_block + content)

    def build_index(self) -> dict[str, dict[str, Any]]:
        """
        Build an index of all notes in the vault.

        Extracts metadata, links, and tags from each note for quick lookup.

        Returns:
            dict: A mapping of note names to their extracted info:
                {
                    "NoteName": {
                        "path": "relative/path/to/note.md",
                        "metadata": {...},
                        "links": [list of linked note names],
                        "tags": [list of tags],
                    },
                    ...
                }
        """
        index = {}
        for file_path in self.list_notes():
            text = file_path.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(text)
            links = extract_wikilinks(body)
            tags = extract_tags(body)
            index[file_path.stem] = {
                "path": str(file_path.relative_to(self.path)),
                "metadata": meta,
                "links": links,
                "tags": tags,
            }
        return index
