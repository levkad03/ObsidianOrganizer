import re
import tempfile
from pathlib import Path

import yaml

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
TAG_PATTERN = re.compile(r"(?<!\w)#([\w/]+)")


def extract_wikilinks(text: str):
    return [m.group(1) for m in WIKILINK_PATTERN.finditer(text)]


def extract_tags(text: str):
    return TAG_PATTERN.findall(text)


def parse_frontmatter(content: str):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_part = parts[1]
            body = parts[2]
            metadata = yaml.safe_load(yaml_part)
            return metadata, body.strip()

    return {}, content


def safe_write(file_path: Path, content: str):
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=file_path.parent)
    temp_file.write(content.encode("utf-8"))
    temp_file.close()
    temp_file_path = Path(temp_file.name)
    temp_file_path.replace(file_path)
