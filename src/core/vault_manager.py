import re
from pathlib import Path
from typing import Any

import yaml

from src.core.note_content import NoteContent
from src.core.utils import (
    parse_frontmatter,
    safe_write,
)
from src.core.vault_index import VaultIndex

ATTACHMENT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".mp3",
    ".mp4",
    ".wav",
    ".webm",
    ".mov",
}


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

        self._index = VaultIndex(self.path)

    @staticmethod
    def _is_attachment(name: str) -> bool:
        """Check if a link points to a common attachment type."""
        return any(name.lower().endswith(ext) for ext in ATTACHMENT_EXTENSIONS)

    def list_notes(self) -> list[Path]:
        """List all markdown notes in the vault."""
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
            metadata (dict | None, optional): Metadata to include as YAML frontmatter.
            content (str, optional): Body text of the note. Defaults to "".

        Returns:
            Path: The path to the created note file.

        Raises:
            FileExistsError: If a note with the given name already exists.
        """
        file_path = self._resolve_path(name)
        if file_path.exists():
            raise FileExistsError(f"Note '{name}' already exists in vault")

        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        yaml_block = f"---\n{yaml.safe_dump(metadata)}---\n\n" if metadata else ""
        safe_write(file_path, yaml_block + content)

        # Invalidate index cache
        self._index.invalidate()

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
        existing_meta = existing_meta or {}

        if metadata:
            existing_meta.update(metadata)

        if content is None:
            new_body = body
        else:
            new_body = (body + "\n" + content) if append else (content + "\n" + body)

        yaml_block = (
            f"---\n{yaml.safe_dump(existing_meta)}---\n\n" if existing_meta else ""
        )
        safe_write(file_path, yaml_block + new_body)

        # Invalidate index cache
        self._index.invalidate()

    def build_index(self, force_rebuild: bool = False) -> dict[str, dict[str, Any]]:
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
        if force_rebuild:
            self._index.invalidate()

        try:
            return self._index.get()
        except RuntimeError:
            # Index not built yet, build it now
            notes = self.list_notes()
            return self._index.build(notes)

    def search_notes(
        self,
        query: str,
        search_content: bool = True,
        search_tags: bool = True,
    ) -> list[dict[str, Any]]:
        """Search notes by keyword in content, title, and tags.

        Args:
            query: The search term (case-insensitive)
            search_content: Whether to search in note body
            search_tags: Whether to search in tags

        Returns:
            List of matching notes with path, title, and matched context
        """

        query_lower = query.lower()
        results = []

        for file_path in self.list_notes():
            try:
                text = file_path.read_text(encoding="utf-8")
                note = NoteContent(file_path, text)
                matches = []

                # Search in filename
                if query_lower in note.name.lower():
                    matches.append("title")

                # Search in content
                if search_content and query_lower in note.content.lower():
                    matches.append("content")

                # Search in tags
                if search_tags and any(query_lower in tag.lower() for tag in note.tags):
                    matches.append("tags")

                if matches:
                    snippet = ""
                    if "content" in matches:
                        idx = note.content.lower().find(query_lower)
                        start = max(0, idx - 50)
                        end = min(len(note.content), idx + len(query) + 50)
                        snippet = "..." + note.content[start:end] + "..."

                    results.append(
                        {
                            "path": str(file_path.relative_to(self.path)),
                            "title": note.name,
                            "matched_in": matches,
                            "snippet": snippet,
                        }
                    )
            except Exception as e:
                print(f"Warning: Failed to search {file_path}: {e}")
                continue

        return results

    def get_backlinks(self, note_name: str) -> list[str]:
        """Find all notes that link to the given name

        Args:
            note_name (str): The name of the note to find backlinks for.

        Returns:
            list[str]: A list of note names that link to the given note.
        """

        index = self.build_index()
        return [name for name, info in index.items() if note_name in info["links"]]

    def find_orphaned_notes(self) -> list[str]:
        """Find notes with no incoming or outgoing links in the vault.

        Returns:
            list[str]: A list of note names that are orphaned.
        """

        index = self.build_index()

        all_notes = set(index.keys())
        linked_to = set()  # Notes that receive links
        has_outlinks = set()  # Notes that have outgoing links

        for name, info in index.items():
            if info["links"]:
                has_outlinks.add(name)
            linked_to.update(info["links"])

        # Orphaned = no outgoing links and no incoming links
        orphaned = all_notes - has_outlinks - linked_to

        return list(orphaned)

    def find_broken_links(self) -> dict[str, list[str]]:
        """Find wikilinks pointing to notes that don't exist

        Returns:
            dict[str, list[str]]: A dictionary where keys are note names and values
            are lists of broken links in those notes.
        """

        index = self.build_index()

        all_notes = set(index.keys())
        broken = {}

        for name, info in index.items():
            missing = [
                link
                for link in info["links"]
                if not self._is_attachment(link) and link not in all_notes
            ]

            if missing:
                broken[name] = missing

        return broken

    def suggest_connections_by_tags(self) -> list[dict]:
        """Find notes that share tags but aren't linked

        Returns:
            list[dict]: A list of suggested connections with shared tags.
        """

        index = self.build_index()
        suggestions = []

        notes = list(index.items())
        for i, (name1, info1) in enumerate(notes):
            tags1 = set(info1["tags"])
            links1 = set(info1["links"])

            for name2, info2 in notes[i + 1 :]:
                if name2 in links1 or name1 in info2["links"]:
                    continue  # Already linked

                tags2 = set(info2["tags"])
                common_tags = tags1 & tags2

                if common_tags:
                    suggestions.append(
                        {
                            "note1": name1,
                            "note2": name2,
                            "common_tags": list(common_tags),
                            "reason": "shared tags",
                        }
                    )

        return suggestions

    def suggest_connections_by_keywords(self, min_overlap: int = 5) -> list[dict]:
        """Find notes with significant word overlap.

        Args:
            min_overlap (int, optional): Minimum number of overlapping words to suggest a connection.

        Returns:
            list[dict]: A list of suggested connections with overlapping keywords.
        """

        index = self.build_index()
        note_words = {}

        # Extract keywords from each note
        for file_path in self.list_notes():
            try:
                text = file_path.read_text(encoding="utf-8")
                _, body = parse_frontmatter(text)
                words = set(re.findall(r"\b\w{4,}\b", body.lower(), re.UNICODE))
                note_words[file_path.stem] = words
            except Exception:
                continue

        suggestions = []
        notes = list(note_words.items())

        for i, (name1, words1) in enumerate(notes):
            links1 = set(index[name1]["links"])

            for name2, words2 in notes[i + 1 :]:
                if name2 in links1 or name1 in index[name2]["links"]:
                    continue

                overlap = words1 & words2
                if len(overlap) >= min_overlap:
                    suggestions.append(
                        {
                            "note1": name1,
                            "note2": name2,
                            "shared_words": len(overlap),
                            "sample_words": list(overlap)[:5],
                            "reason": "keyword overlap",
                        }
                    )

        return suggestions

    def suggest_connections_by_graph(self) -> list[dict]:
        """
        Suggest connections based on link patterns (mutual friends).

        Returns:
            A list of suggested connections via intermediate notes.
        """
        index = self.build_index()
        connections = {}  # {(note1, note2): [via1, via2, ...]}

        for name, info in index.items():
            direct_links = set(info["links"])

            for linked_note in direct_links:
                if self._is_attachment(linked_note) or linked_note not in index:
                    continue

                second_degree = set(index[linked_note]["links"])
                potential = second_degree - direct_links - {name}

                for target in potential:
                    if self._is_attachment(target):
                        continue

                    pair = tuple(sorted([name, target]))  # Normalize pair order
                    if pair not in connections:
                        connections[pair] = []
                    connections[pair].append(linked_note)

        return [
            {
                "note1": pair[0],
                "note2": pair[1],
                "via": via_list,
                "reason": f"connected via {len(via_list)} note(s)",
            }
            for pair, via_list in connections.items()
        ]
