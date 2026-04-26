from pathlib import Path

from mdmirror.bundle import render_tree, write_bundle
from mdmirror.config import ConversionResult


def test_bundle_concatenates_in_order(tmp_path: Path) -> None:
    bundle = tmp_path / "out" / "all.md"
    results = [
        ConversionResult(
            src=tmp_path / "a.py",
            rel=Path("a.py"),
            status="ok",
            content="```python\nprint(1)\n```\n",
        ),
        ConversionResult(
            src=tmp_path / "b.py",
            rel=Path("b.py"),
            status="ok",
            content="```python\nprint(2)\n```\n",
        ),
        ConversionResult(
            src=tmp_path / "c.py", rel=Path("c.py"), status="failed", content="", message="boom"
        ),
    ]
    written = write_bundle(bundle, results, input_root=tmp_path, tree_summary="a.py\nb.py\nc.py")
    text = bundle.read_text()
    assert written == len(text)
    assert "print(1)" in text
    assert "print(2)" in text
    assert "boom" not in text  # failed results not included
    assert "a.py\nb.py\nc.py" in text


def test_render_tree_sorted(tmp_path: Path) -> None:
    paths = [tmp_path / "z.txt", tmp_path / "a" / "b.py", tmp_path / "a.py"]
    (tmp_path / "a").mkdir()
    for p in paths:
        p.touch()
    out = render_tree(paths, tmp_path)
    assert out.splitlines() == ["a.py", "a/b.py", "z.txt"]
