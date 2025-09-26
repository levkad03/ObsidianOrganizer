from pathlib import Path

import pytest

from src.core.vault_manager import ObsidianVault


# Helpers
def make_vault(tmp_path: Path):
    """Creates a fake obsidian vault with .obsidian folder."""
    (tmp_path / ".obsidian").mkdir()
    return tmp_path


def make_note(vault_path: Path, name: str, content: str):
    file = vault_path / f"{name}.md"
    file.write_text(content, encoding="utf-8")
    return file


# Tests
def test_invalid_vault_raises(tmp_path):
    with pytest.raises(ValueError):
        ObsidianVault(tmp_path)


def test_list_notes(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "Note1", "Hello")
    make_note(vault, "Note2", "World")

    obsidian = ObsidianVault(vault)
    notes = obsidian.list_notes()
    assert len(notes) == 2
    assert all(n.suffix == ".md" for n in notes)


def test_read_note_with_frontmatter(tmp_path):
    vault = make_vault(tmp_path)
    content = """---
title: My Note
tags:
  - test
---

Hello World
"""
    make_note(vault, "TestNote", content)
    obsidian = ObsidianVault(vault)
    note = obsidian.read_note("TestNote")

    assert note["metadata"]["title"] == "My Note"
    assert "Hello World" in note["content"]


def test_write_note(tmp_path):
    vault = make_vault(tmp_path)
    content = "Just content"
    file = make_note(vault, "ToUpdate", content)

    obsidian = ObsidianVault(vault)
    obsidian.write_note("ToUpdate", metadata={"author": "me"}, content="New Content")

    text = file.read_text(encoding="utf-8")
    assert "author: me" in text
    assert "New Content" in text


def test_build_index(tmp_path):
    vault = make_vault(tmp_path)
    content = """---
title: IndexTest
---

This links to [[OtherNote]] and has #atag
"""
    make_note(vault, "IndexNote", content)
    make_note(vault, "OtherNote", "No links")

    obsidian = ObsidianVault(vault)
    index = obsidian.build_index()

    assert "IndexNote" in index
    assert index["IndexNote"]["links"] == ["OtherNote"]
    assert "atag" in index["IndexNote"]["tags"]


def test_update_note_appends_and_merges_metadata(tmp_path):
    vault = make_vault(tmp_path)
    content = """---
title: AppendTest
---


Original body
"""
    file = make_note(vault, "AppendNote", content)
    obsidian = ObsidianVault(vault)
    obsidian.update_note(
        "AppendNote",
        content="\nAppended line\n",
        append=True,
        metadata={"tags": ["added"]},
    )

    text = file.read_text(encoding="utf-8")
    assert "Original body" in text
    assert "Appended line" in text
    assert "tags:" in text


def test_update_note_prepends(tmp_path):
    vault = make_vault(tmp_path)
    content = "Body line\n"
    file = make_note(vault, "PrependNote", content)
    obsidian = ObsidianVault(vault)

    obsidian.update_note("PrependNote", content="Intro line\n", append=False)
    text = file.read_text(encoding="utf-8")
    # Prepend should place the new content before existing body
    assert text.startswith("Intro line\n")
    assert "Body line" in text


def test_update_note_metadata_only(tmp_path):
    vault = make_vault(tmp_path)
    content = """---
author: old
---
Body
"""
    file = make_note(vault, "MetaOnly", content)
    obsidian = ObsidianVault(vault)

    obsidian.update_note(
        "MetaOnly", content=None, metadata={"author": "new", "tags": ["x"]}
    )

    text = file.read_text(encoding="utf-8")
    assert "author: new" in text
    assert "tags:" in text
    assert "Body" in text
