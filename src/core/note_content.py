from pathlib import Path

from src.core.utils import extract_tags, extract_wikilinks, parse_frontmatter


class NoteContent:
    """Represents a parsed note with metadata and content."""

    def __init__(self, path: Path, text: str) -> None:
        self.path = path
        self.text = text
        self.metadata, self.content = parse_frontmatter(text)
        self.metadata = self.metadata or {}
        self._links = None
        self._tags = None

    @property
    def name(self) -> str:
        return self.path.stem

    @property
    def links(self) -> list[str]:
        if self._links is None:
            self._links = extract_wikilinks(self.content)

        return self._links

    @property
    def tags(self) -> list[str]:
        if self._tags is None:
            self._tags = extract_tags(self.content)
            # Include frontmatter tags
            if "tags" in self.metadata:
                fm_tags = self.metadata["tags"]
                if isinstance(fm_tags, list):
                    self._tags.extend(fm_tags)

        return self._tags
