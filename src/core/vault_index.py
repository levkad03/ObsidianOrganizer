from pathlib import Path
from typing import Any

from src.core.note_content import NoteContent


class VaultIndex:
    """Manages the vault index with caching."""

    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self._index: dict[str, dict[str, Any]] | None = None

    def invalidate(self) -> None:
        """Clear the cached index."""
        self._index = None

    def build(self, notes: list[Path]) -> dict[str, dict[str, Any]]:
        """Build index from a list of note paths.

        Args:
            notes (list[Path]): List of note file paths.
        Returns:
            dict[str, dict[str, Any]]: The built index.
        """

        if self._index is not None:
            return self._index

        index = {}
        for file_path in notes:
            try:
                text = file_path.read_text(encoding="utf-8")
                note = NoteContent(file_path, text)

                index[note.name] = {
                    "path": str(file_path.relative_to(self.vault_path)),
                    "metadata": note.metadata,
                    "links": note.links,
                    "tags": note.tags,
                    "has_tags": bool(note.tags),
                    "modified_at": file_path.stat().st_mtime,
                    "word_count": len(note.content.split()),
                }
            except Exception as e:
                # Log the error but continue indexing
                print(f"Warning: Failed to index {file_path}: {e}")
                continue

        self._index = index
        return self._index

    def get(self) -> dict[str, dict[str, Any]]:
        """Get the current index, building it if necessary."""

        if self._index is None:
            raise RuntimeError("Index has not been built yet.")

        return self._index
