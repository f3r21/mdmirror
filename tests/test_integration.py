"""Integration tests that exercise the real markitdown pipeline."""

from pathlib import Path

import pytest

from mdmirror.config import MirrorConfig
from mdmirror.converter import convert_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample.docx"


def _config(input_dir: Path) -> MirrorConfig:
    return MirrorConfig(
        input_dir=input_dir,
        output_dir=None,
        bundle_path=None,
        to_stdout=False,
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


@pytest.mark.integration
def test_markitdown_converts_real_docx(tmp_path: Path) -> None:
    assert FIXTURE.is_file(), "fixture missing — regenerate with python-docx"
    src = tmp_path / "sample.docx"
    src.write_bytes(FIXTURE.read_bytes())

    result = convert_file(src, _config(tmp_path))

    assert result.status == "ok", f"status={result.status} msg={result.message}"
    assert "The quick brown fox jumps over the lazy dog" in result.content
    assert "Second paragraph" in result.content
    # Frontmatter is on; markitdown path didn't wrap in a code fence.
    assert "source: sample.docx" in result.content
    assert "```" not in result.content


@pytest.mark.integration
def test_markitdown_text_is_lighter_than_docx(tmp_path: Path) -> None:
    src = tmp_path / "sample.docx"
    src.write_bytes(FIXTURE.read_bytes())

    result = convert_file(src, _config(tmp_path))

    assert result.status == "ok"
    # The docx is ~36KB on disk; the markdown extract is a tiny fraction of that.
    assert len(result.content) < src.stat().st_size // 10
