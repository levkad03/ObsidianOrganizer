from time import time
from typing import Any

from src.core.vault_manager import ObsidianVault


class DashboardService:
    def __init__(self, vault: ObsidianVault) -> None:
        self.vault = vault

    def summary(self) -> dict[str, Any]:
        """Build a high-level dashboard summary for the vault.

        Returns:
            dict[str, Any]: A summary of the vault's contents.
        """

        index = self.vault.build_index()
        now = time()

        # Basic counts
        total_notes = len(index)
        orphaned_notes = self.vault.find_orphaned_notes()
        broken_links = self.vault.find_broken_links()

        untagged_notes = [
            name for name, info in index.items() if not info.get("has_tags", False)
        ]

        # Recent notes (last 7 days)
        SEVEN_DAYS = 7 * 24 * 60 * 60
        recent_notes = [
            {
                "name": name,
                "path": info["path"],
                "modified_at": info["modified_at"],
            }
            for name, info in index.items()
            if now - info["modified_at"] <= SEVEN_DAYS
        ]

        # Backlink counts (for hubs)
        backlink_counts = {name: len(self.vault.get_backlinks(name)) for name in index}

        top_hubs = sorted(
            backlink_counts.items(), key=lambda item: item[1], reverse=True
        )[:5]

        return {
            "vault": {
                "path": str(self.vault.path),
            },
            "stats": {
                "total_notes": total_notes,
                "orphaned_notes": len(orphaned_notes),
                "broken_links": sum(len(v) for v in broken_links.values()),
                "untagged_notes": len(untagged_notes),
                "recent_notes": len(recent_notes),
            },
            "recent_notes": recent_notes[:10],
            "top_hubs": [
                {"name": name, "backlinks": count} for name, count in top_hubs
            ],
            "generated_at": now,
        }
