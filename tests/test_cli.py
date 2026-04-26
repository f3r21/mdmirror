from pathlib import Path

from mdmirror.cli import main


def test_default_writes_claude_bundle(sample_tree: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_tree)])
    assert rc == 0
    bundle = tmp_path / f"{sample_tree.name}.claude.md"
    assert bundle.is_file()
    text = bundle.read_text(encoding="utf-8")
    assert "Context bundle" in text
    assert "src/main.py" in text
    assert "def hi" in text
    # No tree should be written by default.
    assert not (sample_tree.parent / f"{sample_tree.name}_md").exists()


def test_default_dot_from_inside_folder(sample_tree: Path, monkeypatch) -> None:
    """`mdmirror .` from inside a folder writes <name>.claude.md as a sibling."""
    monkeypatch.chdir(sample_tree)
    rc = main(["."])
    assert rc == 0
    bundle = sample_tree.parent / f"{sample_tree.name}.claude.md"
    assert bundle.is_file()
    assert "src/main.py" in bundle.read_text(encoding="utf-8")
    # Bundle must NOT be inside the input dir.
    assert not (sample_tree / f"{sample_tree.name}.claude.md").exists()


def test_default_with_explicit_bundle_path(sample_tree: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "ctx.md"
    rc = main([str(sample_tree), str(bundle)])
    assert rc == 0
    assert bundle.is_file()
    assert "def hi" in bundle.read_text(encoding="utf-8")


def test_tree_flag_writes_mirror_default_path(sample_tree: Path) -> None:
    rc = main([str(sample_tree), "--tree"])
    assert rc == 0
    out_root = sample_tree.parent / f"{sample_tree.name}_md"
    assert out_root.is_dir()
    assert (out_root / "src" / "main.py.md").is_file()
    assert (out_root / "README.md").is_file()
    assert not (out_root / "node_modules").exists()
    assert not (out_root / ".git").exists()


def test_tree_flag_with_explicit_output(sample_tree: Path, tmp_path: Path) -> None:
    out_root = tmp_path / "ghost"
    rc = main([str(sample_tree), str(out_root), "--tree"])
    assert rc == 0
    assert (out_root / "src" / "main.py.md").is_file()


def test_tree_with_bundle_flag_writes_both(sample_tree: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out_root = tmp_path / "ghost"
    rc = main([str(sample_tree), str(out_root), "--tree", "--bundle"])
    assert rc == 0
    assert (out_root / "src" / "main.py.md").is_file()
    bundle = tmp_path / f"{sample_tree.name}.claude.md"
    assert bundle.is_file()


def test_dry_run_writes_nothing(sample_tree: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main([str(sample_tree), "--dry-run"])
    assert rc == 0
    assert not (tmp_path / f"{sample_tree.name}.claude.md").exists()


def test_refuses_tree_output_inside_input(sample_tree: Path) -> None:
    inside = sample_tree / "ghost"
    rc = main([str(sample_tree), str(inside), "--tree"])
    assert rc == 2


def test_stdout_writes_bundle_to_stdout(sample_tree: Path, capsys) -> None:
    rc = main([str(sample_tree), "--stdout"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Context bundle" in captured.out
    assert "src/main.py" in captured.out
    assert "def hi" in captured.out
    # No bundle file should be written.
    assert not Path(f"{sample_tree.name}.claude.md").exists()


def test_stdout_with_output_arg_errors(sample_tree: Path, tmp_path: Path) -> None:
    rc = main([str(sample_tree), str(tmp_path / "x.md"), "--stdout"])
    assert rc == 2


def test_stdout_with_tree_errors(sample_tree: Path) -> None:
    rc = main([str(sample_tree), "--tree", "--stdout"])
    assert rc == 2
