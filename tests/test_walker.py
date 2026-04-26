from pathlib import Path

from mdmirror.ignore import build_spec, load_gitignore
from mdmirror.walker import walk_files


def _names(root: Path, paths: list[Path]) -> set[str]:
    return {p.relative_to(root).as_posix() for p in paths}


def test_default_ignore_skips_node_modules_and_git(sample_tree: Path) -> None:
    spec = build_spec(use_default=True, use_gitignore_spec=None, extra_patterns=())
    found = list(walk_files(sample_tree, spec=spec, include_hidden=False, follow_symlinks=False))
    names = _names(sample_tree, found)
    assert "node_modules/pkg/index.js" not in names
    assert ".git/HEAD" not in names
    assert "src/main.py" in names


def test_gitignore_honored(sample_tree: Path) -> None:
    gi = load_gitignore(sample_tree)
    spec = build_spec(use_default=False, use_gitignore_spec=gi, extra_patterns=())
    found = list(walk_files(sample_tree, spec=spec, include_hidden=True, follow_symlinks=False))
    names = _names(sample_tree, found)
    assert "ignored_dir/secret.txt" not in names
    assert "trace.log" not in names
    assert "src/main.py" in names


def test_include_hidden_off_skips_dotfiles(sample_tree: Path) -> None:
    spec = build_spec(use_default=False, use_gitignore_spec=None, extra_patterns=())
    found = list(walk_files(sample_tree, spec=spec, include_hidden=False, follow_symlinks=False))
    names = _names(sample_tree, found)
    assert ".gitignore" not in names
    assert "src/main.py" in names


def test_skip_pattern_extra(sample_tree: Path) -> None:
    spec = build_spec(use_default=True, use_gitignore_spec=None, extra_patterns=("*.json",))
    found = list(walk_files(sample_tree, spec=spec, include_hidden=False, follow_symlinks=False))
    names = _names(sample_tree, found)
    assert "docs/data.json" not in names
