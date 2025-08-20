import re
import tempfile
from pathlib import Path

import yaml

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
TAG_PATTERN = re.compile(r"(?<!\w)#([\w/]+)")


def extract_wikilinks(text: str):
    """
    Extract Obsidian-style wikilinks from a text string.

    A wikilink has the format:
        [[Note Name]]
        [[Note Name|Display Text]]
        [[Note Name#Heading]]

    Args:
        text (str): The markdown content to search.

    Returns:
        list[str]: A list of linked note names (the target part of the link).
    """
    return [m.group(1) for m in WIKILINK_PATTERN.finditer(text)]


def extract_tags(text: str):
    """
    Extract tags from markdown text.

    Tags are written as:
        #tag
        #nested/tag

    Args:
        text (str): The markdown content to search.

    Returns:
        list[str]: A list of tags (without the leading #).
    """
    return TAG_PATTERN.findall(text)


def parse_frontmatter(content: str):
    """
    Parse YAML frontmatter from markdown content.

    Frontmatter is expected in the format:
        ---
        key: value
        ...
        ---

    Args:
        content (str): Full note content (including frontmatter and body).

    Returns:
        tuple[dict, str]:
            - metadata (dict): Parsed YAML metadata if present, else {}.
            - body (str): Markdown content without the frontmatter.
    """
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_part = parts[1]
            body = parts[2]
            metadata = yaml.safe_load(yaml_part)
            return metadata, body.strip()

    return {}, content


def safe_write(file_path: Path, content: str):
    """
    Safely write text content to a file.

    Uses a temporary file and atomic replace to avoid corruption
    if the process crashes mid-write.

    Args:
        file_path (Path): Destination file path.
        content (str): The text content to write.

    Side Effects:
        - Overwrites the target file with new content.
        - Creates and deletes a temporary file in the same directory.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=file_path.parent)
    temp_file.write(content.encode("utf-8"))
    temp_file.close()
    temp_file_path = Path(temp_file.name)
    temp_file_path.replace(file_path)
