import re

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
