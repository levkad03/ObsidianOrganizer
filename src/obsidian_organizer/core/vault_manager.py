from pathlib import Path

import yaml

from obsidian_organizer.core.utils import (
    extract_tags,
    extract_wikilinks,
    parse_frontmatter,
)


class ObsidianVault:
    def __init__(self, path: Path):
        self.path = path

        if not (self.path / ".obsidian").exists():
            raise ValueError("Not a valid obsidian vault")

    def list_notes(self):
        return list(self.path.glob("**/*.md"))

    def _resolve_path(self, name: str) -> Path:
        if not name.endswith(".md"):
            name += ".md"

        file_path = (self.path / name).resolve()

        if not str(file_path).startswith(str(self.path.resolve())):
            raise ValueError("Attempted access outside of vault")

        return file_path

    def read_note(self, name: str):
        file_path = self._resolve_path(name)
        if not file_path.exists():
            raise FileNotFoundError(f"Note '{name}' not found in vault")
        text = file_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        return {"metadata": meta, "content": body}

    def write_note(self, name: str, metadata: dict, content: str):
        yaml_block = f"---\n{yaml.safe_dump(metadata)}---\n\n" if metadata else ""
        file_path = self._resolve_path(name)
        if not file_path.exists():
            raise FileNotFoundError(f"Note '{name}' not found in vault")
        file_path.write_text(yaml_block + content, encoding="utf-8")

    def build_index(self):
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
