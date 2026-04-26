from pathlib import Path

from mdmirror.config import MirrorConfig
from mdmirror.converter import convert_file


def _config(input_dir: Path, **overrides) -> MirrorConfig:
    base = dict(
        input_dir=input_dir,
        output_dir=input_dir.parent / "out",
        bundle_path=None,
        overwrite=True,
        dry_run=False,
        workers=1,
        skip_patterns=(),
        include_hidden=False,
        follow_symlinks=False,
        use_default_ignore=True,
        use_gitignore=True,
        add_frontmatter=True,
        fence_code=True,
        quiet=False,
        verbose=False,
    )
    base.update(overrides)
    return MirrorConfig(**base)


def test_python_file_gets_python_fence(tmp_path: Path) -> None:
    src = tmp_path / "main.py"
    src.write_text("def f():\n    return 1\n")
    result = convert_file(src, _config(tmp_path))
    assert result.status == "ok"
    assert "```python" in result.content
    assert "def f():" in result.content
    assert "source: main.py" in result.content


def test_typescript_uses_ts_fence(tmp_path: Path) -> None:
    src = tmp_path / "x.ts"
    src.write_text("export const a = 1\n")
    result = convert_file(src, _config(tmp_path))
    assert "```ts" in result.content


def test_markdown_passes_through(tmp_path: Path) -> None:
    src = tmp_path / "README.md"
    src.write_text("# Title\n")
    result = convert_file(src, _config(tmp_path))
    assert result.status == "ok"
    # Body present, no triple-fence wrapping.
    assert "# Title" in result.content
    assert "```" not in result.content.replace("```", "", 0)


def test_no_frontmatter_when_disabled(tmp_path: Path) -> None:
    src = tmp_path / "x.py"
    src.write_text("x = 1\n")
    result = convert_file(src, _config(tmp_path, add_frontmatter=False))
    assert "source:" not in result.content
    assert "```python" in result.content


def test_no_fence_when_disabled_falls_to_markitdown(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "x.py"
    src.write_text("print(1)\n")

    captured = {}

    class FakeResult:
        text_content = "fake markdown body"

    class FakeMD:
        def convert(self, path):
            captured["path"] = path
            return FakeResult()

    import mdmirror.converter as conv

    monkeypatch.setattr(
        conv, "_markitdown_convert", lambda p: FakeMD().convert(str(p)).text_content
    )

    result = convert_file(src, _config(tmp_path, fence_code=False))
    assert result.status == "ok"
    assert "fake markdown body" in result.content


def test_failed_conversion_records_message(tmp_path: Path, monkeypatch) -> None:
    src = tmp_path / "weird.docx"
    src.write_text("not really a docx")

    import mdmirror.converter as conv

    def boom(path):
        raise RuntimeError("nope")

    monkeypatch.setattr(conv, "_markitdown_convert", boom)

    result = convert_file(src, _config(tmp_path))
    assert result.status == "failed"
    assert "nope" in result.message
