import re
from pathlib import Path
from typing import Any

import yaml

from src.core.utils import (
    extract_tags,
    extract_wikilinks,
    parse_frontmatter,
    safe_write,
)

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

    def _is_attachment(self, name: str) -> bool:
        """Check if a link points to a common attachment type.

        Args:
            name (str): The name of the link.

        Returns:
            bool: True if the link is an attachment, False otherwise.
        """
        return any(name.lower().endswith(ext) for ext in ATTACHMENT_EXTENSIONS)

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
            text = file_path.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(text)

            matches = []

            # Search in filename
            if query_lower in file_path.stem.lower():
                matches.append("title")

            # Search in content
            if search_content and query_lower in body.lower():
                matches.append("content")

            # Search in tags
            if search_tags:
                tags = extract_tags(body)

                # Also check frontmatter tags
                if meta and "tags" in meta:
                    fm_tags = meta["tags"]
                    if isinstance(fm_tags, list):
                        tags.extend(fm_tags)

                if any(query_lower in tag.lower() for tag in tags):
                    matches.append("tags")

            if matches:
                # Extract a snippet around the match
                snippet = ""
                if "content" in matches:
                    idx = body.lower().find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(body), idx + len(body) + 50)
                    snippet = "..." + body[start:end] + "..."

                results.append(
                    {
                        "path": str(file_path.relative_to(self.path)),
                        "title": file_path.stem,
                        "matched_in": matches,
                        "snippet": snippet,
                    }
                )

        return results

    def get_backlinks(self, note_name: str) -> list[str]:
        """Find all notes that link to the given name

        Args:
            note_name (str): The name of the note to find backlinks for.

        Returns:
            list[str]: A list of note names that link to the given note.
        """

        index = self.build_index()
        backlinks = []

        for name, info in index.items():
            if note_name in info["links"]:
                backlinks.append(name)

        return backlinks

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
            missing = []
            for link in info["links"]:
                # Skip if it's an attachment
                if self._is_attachment(link):
                    continue
                # Check if note exists
                if link not in all_notes:
                    missing.append(link)

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
            min_overlap (int, optional): Minimum number of overlapping words to suggest a connection. Defaults to 5.

        Returns:
            list[dict]: A list of suggested connections with overlapping keywords.
        """

        index = self.build_index()
        note_words = {}

        # Extract keywords from each note
        for file_path in self.list_notes():
            text = file_path.read_text(encoding="utf-8")
            _, body = parse_frontmatter(text)
            # Simple word extraction (can be improved with stopwords removal)
            words = set(re.findall(r"\b[a-zA-Z]{4,}\b", body.lower()))
            note_words[file_path.stem] = words

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
        """Suggest connections based on link patterns.

        Returns:
            list[dict]: List of suggested connections based on graph analysis.
        """

        index = self.build_index()
        suggestions = []

        for name, info in index.items():
            direct_links = set(info["links"])

            # Find "friends of friends"
            for linked_note in direct_links:
                if self._is_attachment(linked_note):
                    continue

                if linked_note in index:
                    second_degree = set(index[linked_note]["links"])

                    # Notes linked by my links, but not by me
                    potential = second_degree - direct_links - {name}

                    for target in potential:
                        if self._is_attachment(target):
                            continue  # Skip attachments as targets

                        suggestions.append(
                            {
                                "note1": name,
                                "note2": target,
                                "via": linked_note,
                                "reason": f"both connected to {linked_note}",
                            }
                        )

        return suggestions
