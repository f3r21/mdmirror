from pathlib import Path

from mdmirror.config import MirrorConfig
from mdmirror.runner import run


def _config(input_dir: Path, output_dir: Path | None = None, **overrides) -> MirrorConfig:
    base = dict(
        input_dir=input_dir,
        output_dir=output_dir,
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
        quiet=True,
        verbose=False,
    )
    base.update(overrides)
    return MirrorConfig(**base)


def _read_tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in root.rglob("*")
        if p.is_file()
    }


def test_parallel_matches_sequential(sample_tree: Path, tmp_path: Path) -> None:
    seq_out = tmp_path / "seq"
    par_out = tmp_path / "par"
    run(_config(sample_tree, seq_out, workers=1))
    run(_config(sample_tree, par_out, workers=2))
    assert _read_tree(seq_out) == _read_tree(par_out)


def test_parallel_bundle_sorted_by_path(sample_tree: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "ctx.md"
    run(_config(sample_tree, bundle_path=bundle, workers=2))
    text = bundle.read_text(encoding="utf-8")

    # Pull every "source: ..." line in order it appears in the bundle.
    sources = [
        line.split("source:", 1)[1].strip()
        for line in text.splitlines()
        if line.startswith("source:")
    ]
    assert sources == sorted(sources)
    assert "src/main.py" in sources
    assert "README.md" in sources


def test_token_count_populated(sample_tree: Path, tmp_path: Path) -> None:
    summary = run(_config(sample_tree, tmp_path / "out"))
    assert summary.token_count > 0
    # Reasonable upper bound: small fixture tree.
    assert summary.token_count < 5000
