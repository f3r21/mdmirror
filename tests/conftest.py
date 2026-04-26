from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def sample_tree(tmp_path: Path) -> Path:
    """A small fixture tree with code, text, hidden files, and ignored dirs."""
    root = tmp_path / "input project"  # space in name on purpose
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / ".git").mkdir()

    (root / "README.md").write_text("# Hello\nworld\n")
    (root / "src" / "main.py").write_text("def hi():\n    return 1\n")
    (root / "src" / "util.ts").write_text("export const x = 1\n")
    (root / "docs" / "notes.txt").write_text("just some notes\n")
    (root / "docs" / "data.json").write_text('{"a": 1}\n')
    (root / "node_modules" / "pkg" / "index.js").write_text("module.exports = 1\n")
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (root / ".gitignore").write_text("ignored_dir/\n*.log\n")
    (root / "ignored_dir").mkdir()
    (root / "ignored_dir" / "secret.txt").write_text("nope\n")
    (root / "trace.log").write_text("noisy\n")

    return root
