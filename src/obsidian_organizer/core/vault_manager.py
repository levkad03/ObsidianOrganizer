from pathlib import Path

import yaml

from obsidian_organizer.core.utils import parse_frontmatter


class ObsidianVault:
    def __init__(self, path: Path):
        self.path = path

        if not (self.path / ".obsidian").exists():
            raise ValueError("Not a valid obsidian vault")

    def list_notes(self):
        return list(self.path.glob("**/*.md"))

    def read_note(self, name: str):
        file_path = self.path / f"{name}.md"
        text = file_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        return {"metadata": meta, "content": body}

    def write_note(self, name: str, metadata: dict, content: str):
        yaml_block = f"---\n{yaml.safe_dump(metadata)}---\n\n" if metadata else ""
        file_path = self.path / f"{name}.md"
        file_path.write_text(yaml_block + content, encoding="utf-8")
