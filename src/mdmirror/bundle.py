from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import IO

from mdmirror.config import ConversionResult

SEPARATOR = "\n\n<!-- ────────────────────────────── -->\n\n"


def write_bundle_to(
    out: IO[str],
    results: Iterable[ConversionResult],
    *,
    input_root: Path,
    tree_summary: str | None = None,
) -> int:
    """Write all successful results to `out` (any text file-like). Returns chars written."""
    written = 0
    header = _bundle_header(input_root, tree_summary)
    out.write(header)
    written += len(header)
    first = True
    for result in results:
        if result.status not in ("ok", "empty"):
            continue
        if not first:
            out.write(SEPARATOR)
            written += len(SEPARATOR)
        out.write(result.content)
        written += len(result.content)
        first = False
    return written


def write_bundle(
    bundle_path: Path,
    results: Iterable[ConversionResult],
    *,
    input_root: Path,
    tree_summary: str | None = None,
) -> int:
    """Concatenate all successful results into one .md file. Returns chars written."""
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with bundle_path.open("w", encoding="utf-8", newline="\n") as fh:
        return write_bundle_to(fh, results, input_root=input_root, tree_summary=tree_summary)


def _bundle_header(input_root: Path, tree_summary: str | None) -> str:
    lines = [
        f"# Context bundle: {input_root.name}",
        "",
        f"Source root: `{input_root}`",
        "",
    ]
    if tree_summary:
        lines.extend(
            [
                "## File tree",
                "",
                "```",
                tree_summary.rstrip(),
                "```",
                "",
            ]
        )
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_tree(paths: list[Path], input_root: Path) -> str:
    """Plain indented file list, sorted, relative to input_root."""
    rels = sorted(p.relative_to(input_root).as_posix() for p in paths)
    return "\n".join(rels)
