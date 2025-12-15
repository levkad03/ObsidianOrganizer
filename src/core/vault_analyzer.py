import re
from typing import Any

from src.core.utils import parse_frontmatter
from src.core.vault_manager import ObsidianVault


class VaultAnalyzer:
    """
    Provides advanced analysis and connection suggestions for an Obsidian vault.

    Separates graph analysis, pattern detection, and recommendation logic
    from core vault operations.
    """

    def __init__(self, vault: ObsidianVault) -> None:
        self.vault = vault
        self._cached_index = None

    @property
    def index(self) -> dict[str, dict[str, Any]]:
        """Get the vault index, building it if necessary."""
        if self._cached_index is None:
            self._cached_index = self.vault.build_index()

        return self._cached_index

    def invalidate_cache(self) -> None:
        """Clear cached analysis data."""
        self._cached_index = None

    def get_backlinks(self, note_name: str) -> list[str]:
        """
        Find all notes that link to the given note.

        Args:
            note_name: The name of the note to find backlinks for.

        Returns:
            A list of note names that link to the given note.
        """

        return [name for name, info in self.index.items() if note_name in info["links"]]

    def find_orphaned_notes(self) -> list[str]:
        """
        Find notes with no incoming or outgoing links.

        Returns:
            A list of note names that are orphaned.
        """

        all_notes = set(self.index.keys())
        linked_to = set()
        has_outlinks = set()

        for name, info in self.index.items():
            if info["links"]:
                has_outlinks.add(name)
                linked_to.update(info["links"])

        orphaned = all_notes - linked_to - has_outlinks
        return list(orphaned)

    def find_broken_links(self) -> dict[str, list[str]]:
        """
        Find wikilinks pointing to notes that don't exist.

        Returns:
            A dictionary mapping note names to their broken links.
        """

        all_notes = set(self.index.keys())
        broken = {}

        for name, info in self.index.items():
            missing = [
                link
                for link in info["links"]
                if not self.vault._is_attachment(link) and link not in all_notes
            ]
            if missing:
                broken[name] = missing

        return broken

    def suggest_connections_by_tags(self) -> list[dict]:
        """Find notes that share tags but aren't linked

        Returns:
            list[dict]: A list of suggested connections with shared tags.
        """

        suggestions = []
        notes = list(self.index.items())

        for i, (name1, info1) in enumerate(notes):
            tags1 = set(info1["tags"])
            links1 = set(info1["links"])

            for name2, info2 in notes[i + 1 :]:
                # Skip if already linked
                if name2 in links1 or name1 in info2["links"]:
                    continue

                common_tags = tags1 & set(info2["tags"])
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
        """
        Find notes with significant word overlap.

        Args:
            min_overlap: Minimum number of overlapping words.

        Returns:
            A list of suggested connections with overlapping keywords.
        """

        note_words = {}

        for file_path in self.vault.list_notes():
            try:
                text = file_path.read_text(encoding="utf-8")
                _, body = parse_frontmatter(text)
                words = set(re.findall(r"\b\w{4,}\b", body.lower(), re.UNICODE))
                note_words[file_path.stem] = words
            except Exception as e:
                continue

        suggestions = []
        notes = list(note_words.items())

        for i, (name1, words1) in enumerate(notes):
            links1 = set(self.index[name1]["links"])

            for name2, words2 in notes[i + 1 :]:
                # Skip if already linked
                if name2 in links1 or name1 in self.index[name2]["links"]:
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
        Suggest connections based on graph proximity.

        Returns:
            A list of suggested connections based on graph analysis.
        """

        connections = {}

        for name, info in self.index.items():
            direct_links = set(info["links"])

            for linked_note in direct_links:
                if (
                    self.vault._is_attachment(linked_note)
                    or linked_note not in self.index
                ):
                    continue

                second_degree = set(self.index[linked_note]["links"])
                potential = second_degree - direct_links - {name}

                for target in potential:
                    if self.vault._is_attachment(target):
                        continue

                    pair = tuple(sorted([name, target]))
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
