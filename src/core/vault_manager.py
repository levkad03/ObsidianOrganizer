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

        # Allow folder separators in the note name, normalize via Path
        file_path = (self.path / Path(name)).resolve()

        try:
            # prefer Path.relative_to for robust containment check
            file_path.relative_to(self.path.resolve())
        except Exception:
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

    def create_note(
        self, name: str, metadata: dict | None = None, content: str = ""
    ) -> Path:
        """Create a new note in the vault and write optional metadata and content.

        Args:
            name (str): Note name (with or without .md).
            metadata (dict | None, optional): Metadata to include as YAML frontmatter. Defaults to None.
            content (str, optional): Body text of the note. Defaults to "".

        Returns:
            Path: The path to the created note file.

        Raises:
            FileExistsError: If a note with the given name already exists.
        """
        yaml_block = f"---\n{yaml.safe_dump(metadata)}---\n\n" if metadata else ""
        file_path = self._resolve_path(name)
        if file_path.exists():
            raise FileExistsError(f"Note '{name}' already exists in vault")

        # Ensure parent directories exist for foldered notes
        parent = file_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

        safe_write(file_path, yaml_block + content)
        return file_path

    def update_note(
        self,
        name: str,
        content: str | None = None,
        append: bool = True,
        metadata: dict | None = None,
    ) -> None:
        """Update an existing note without removing its current body.

        - If `content` is provided it will be appended (default) or prepended.
        - If `metadata` is provided it will be merged into existing frontmatter.
        - Frontmatter and body are preserved and written atomically.

        Args:
            name (str): Note name (with or without .md).
            content (str | None, optional): Text to add to the note body. If None, only metadata is updated.
            append (bool, optional): If True append after existing body, otherwise prepend.
            metadata (dict | None, optional): Metadata to merge into existing frontmatter.

        Raises:
            FileNotFoundError: If the note does not exist in the vault.
        """

        file_path = self._resolve_path(name)

        if not file_path.exists():
            raise FileNotFoundError(f"Note '{name}' not found in vault")

        text = file_path.read_text(encoding="utf-8")
        existing_meta, body = parse_frontmatter(text)

        # Ensure metadata is a dict
        existing_meta = existing_meta or {}
        if metadata:
            # Merge provided metadata into existing, override existing keys
            existing_meta.update(metadata)

        # If no content provided, just rewrite frontmatter preserving body
        if content is None:
            new_body = body
        else:
            new_body = (body + "\n" + content) if append else (content + "\n" + body)

        yaml_block = (
            f"---\n{yaml.safe_dump(existing_meta)}---\n\n" if existing_meta else ""
        )

        safe_write(file_path, yaml_block + new_body)

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
