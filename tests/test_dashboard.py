from pathlib import Path

from src.core.vault_manager import ObsidianVault
from src.services.dashboard_service import DashboardService


def make_vault(tmp_path: Path):
    (tmp_path / ".obsidian").mkdir()
    return tmp_path


def make_note(vault_path: Path, name: str, content: str):
    file = vault_path / f"{name}.md"
    file.write_text(content, encoding="utf-8")
    return file


def test_dashboard_summary_structure(tmp_path):
    vault_path = make_vault(tmp_path)
    make_note(vault_path, "Note1", "Hello")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)
    summary = service.summary()

    assert "vault" in summary
    assert "stats" in summary
    assert "recent_notes" in summary
    assert "top_hubs" in summary
    assert "generated_at" in summary


def test_dashboard_total_notes(tmp_path):
    vault_path = make_vault(tmp_path)
    make_note(vault_path, "Note1", "Hello")
    make_note(vault_path, "Note2", "World")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)
    summary = service.summary()

    assert summary["stats"]["total_notes"] == 2


def test_dashboard_orphaned_notes(tmp_path):
    vault_path = make_vault(tmp_path)
    make_note(vault_path, "Note1", "Links to [[Note2]]")
    make_note(vault_path, "Note2", "No links")
    make_note(vault_path, "Orphan", "I am alone")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)

    summary = service.summary()

    assert summary["stats"]["orphaned_notes"] == 1


def test_dashboard_broken_links(tmp_path):
    vault_path = make_vault(tmp_path)

    make_note(vault_path, "Good", "Links to [[Existing]]")
    make_note(vault_path, "Existing", "Here")
    make_note(vault_path, "Broken", "Links to [[Missing]]")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)

    summary = service.summary()

    assert summary["stats"]["broken_links"] == 1


def test_dashboard_untagged_notes(tmp_path):
    vault_path = make_vault(tmp_path)

    make_note(
        vault_path,
        "Tagged",
        "---\ntags: [test]\n---\ncontent",
    )
    make_note(vault_path, "Untagged1", "No tags here")
    make_note(vault_path, "Untagged2", "Also no tags")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)

    summary = service.summary()

    assert summary["stats"]["untagged_notes"] == 2


def test_dashboard_recent_notes(tmp_path):
    vault_path = make_vault(tmp_path)

    make_note(vault_path, "Note1", "A")
    make_note(vault_path, "Note2", "B")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)

    summary = service.summary()

    assert summary["stats"]["recent_notes"] == 2
    assert len(summary["recent_notes"]) == 2


def test_dashboard_top_hubs(tmp_path):
    vault_path = make_vault(tmp_path)

    make_note(vault_path, "NoteA", "Links to [[NoteB]]")
    make_note(vault_path, "NoteB", "No links")
    make_note(vault_path, "NoteC", "Links to [[NoteB]]")

    obsidian = ObsidianVault(vault_path)
    service = DashboardService(obsidian)

    summary = service.summary()

    hubs = summary["top_hubs"]

    assert hubs[0]["name"] == "NoteB"
    assert hubs[0]["backlinks"] == 2
