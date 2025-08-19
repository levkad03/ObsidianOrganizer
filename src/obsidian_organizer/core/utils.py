import yaml


def parse_frontmatter(content: str):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_part = parts[1]
            body = parts[2]
            metadata = yaml.safe_load(yaml_part)
            return metadata, body.strip()

    return {}, content
