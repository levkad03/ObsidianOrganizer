from time import time
from typing import Any

from src.core.vault_manager import ObsidianVault


class DashboardService:
    RECENT_DAYS = 7

    def __init__(self, vault: ObsidianVault) -> None:
        self.vault = vault
        self._index = self.vault.build_index()

    def summary(self) -> dict[str, Any]:
        """Build a high-level dashboard summary for the vault.

        Returns:
            dict[str, Any]: A summary of the vault's contents.
        """

        now = time()

        return {
            "vault": {
                "path": str(self.vault.path),
            },
            "stats": self.get_stats(now),
            "recent_notes": self.get_recent_notes(now),
            "top_hubs": self.get_top_hubs(),
            "generated_at": now,
        }

    def get_stats(self, now: float) -> dict[str, int]:
        """Get various statistics about the vault.

        Args:
            now (float): The current time as a timestamp.

        Returns:
            dict[str, int]: A dictionary containing various statistics about the vault.
        """

        orphaned = self.vault.find_orphaned_notes()
        broken = self.vault.find_broken_links()
        untagged = self.get_untagged_notes()
        recent = self.get_recent_notes(now)

        return {
            "total_notes": len(self._index),
            "orphaned_notes": len(orphaned),
            "broken_links": sum(len(v) for v in broken.values()),
            "untagged_notes": len(untagged),
            "recent_notes": len(recent),
        }

    def get_untagged_notes(self) -> list[str]:
        """Get a list of notes that do not have any tags.

        Returns:
            list[str]: A list of note names that are untagged.
        """
        return [
            name
            for name, info in self._index.items()
            if not info.get("has_tags", False)
        ]

    def get_recent_notes(self, now: float) -> list[dict[str, Any]]:
        """Get a list of notes that have been modified recently.

        Args:
            now (float): The current time as a timestamp.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing information about
            recently modified notes.
        """
        threshold = self.RECENT_DAYS * 24 * 60 * 60

        return [
            {
                "name": name,
                "path": info["path"],
                "modified_at": info["modified_at"],
            }
            for name, info in self._index.items()
            if now - info["modified_at"] <= threshold
        ]

    def get_top_hubs(self, limit: int = 5) -> list[dict[str, int]]:
        """Get the top notes with the most backlinks.

        Args:
            limit (int, optional): The maximum number of top hubs to return.

        Returns:
            list[dict[str, int]]: A list of dictionaries containing the top hubs and
            their backlink counts.
        """
        backlink_counts = {
            name: len(self.vault.get_backlinks(name)) for name in self._index
        }

        sorted_hubs = sorted(
            backlink_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            {"note": name, "backlinks": count} for name, count in sorted_hubs[:limit]
        ]
