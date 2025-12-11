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


def test_create_note_with_content_and_metadata(tmp_path):
    vault = make_vault(tmp_path)
    obsidian = ObsidianVault(vault)

    file = obsidian.create_note(
        "NewNote", metadata={"author": "tester"}, content="Hello Obsidian\n"
    )

    assert file.exists()
    text = file.read_text(encoding="utf-8")
    assert "author: tester" in text
    assert "Hello Obsidian" in text


def test_create_note_existing_raises(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "ExistNote", "Already here")

    obsidian = ObsidianVault(vault)
    with pytest.raises(FileExistsError):
        obsidian.create_note("ExistNote", content="New content")


# Search tests
def test_search_notes_by_title(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "MachineLearning", "Some content")
    make_note(vault, "Cooking", "Recipe content")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("machine")

    assert len(results) == 1
    assert results[0]["title"] == "MachineLearning"
    assert "title" in results[0]["matched_in"]


def test_search_notes_by_content(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "Note1", "This note talks about transformers and AI")
    make_note(vault, "Note2", "This note is about cooking")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("transformers")

    assert len(results) == 1
    assert results[0]["title"] == "Note1"
    assert "content" in results[0]["matched_in"]
    assert "transformers" in results[0]["snippet"].lower()


def test_search_notes_by_inline_tags(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "TaggedNote", "Content with #machinelearning tag")
    make_note(vault, "OtherNote", "No relevant tags #cooking")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("machinelearning")

    assert len(results) == 1
    assert results[0]["title"] == "TaggedNote"
    assert "tags" in results[0]["matched_in"]


def test_search_notes_by_frontmatter_tags(tmp_path):
    vault = make_vault(tmp_path)
    content = """---
tags:
  - python
  - programming
---

Some content here
"""
    make_note(vault, "PythonNote", content)
    make_note(vault, "OtherNote", "Nothing relevant here")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("python")

    assert len(results) == 1
    assert results[0]["title"] == "PythonNote"
    assert "tags" in results[0]["matched_in"]


def test_search_notes_no_results(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "Note1", "Some content")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("nonexistent")

    assert len(results) == 0


def test_search_notes_multiple_matches(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "AINote", "Content about AI and neural networks")
    make_note(vault, "Note2", "AI is transforming the world #ai")
    make_note(vault, "Note3", "No match here")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("ai")

    assert len(results) == 2
    titles = [r["title"] for r in results]
    assert "AINote" in titles
    assert "Note2" in titles


def test_search_notes_matches_in_multiple_places(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "Python", "Content about python programming #python")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("python")

    assert len(results) == 1
    matched_in = results[0]["matched_in"]
    assert "title" in matched_in
    assert "content" in matched_in
    assert "tags" in matched_in


def test_search_notes_content_only(tmp_path):
    vault = make_vault(tmp_path)
    make_note(vault, "TestNote", "Content with #testtag")

    obsidian = ObsidianVault(vault)
    results = obsidian.search_notes("testtag", search_content=True, search_tags=False)

    # Should match in content (since #testtag is part of the text) but not report tags
    assert len(results) == 1
    assert "tags" not in results[0]["matched_in"]
