from __future__ import annotations

from pathlib import Path

PASSTHROUGH_SUFFIXES = {".md", ".markdown"}


def to_output_path(src: Path, input_root: Path, output_root: Path) -> Path:
    """Map a source file to its mirrored output location.

    `report.docx` -> `report.docx.md` (avoids collisions when sibling
    files share a stem). Already-markdown files keep their original name.
    """
    rel = src.relative_to(input_root)
    if src.suffix.lower() in PASSTHROUGH_SUFFIXES:
        return output_root / rel
    return output_root / rel.with_name(rel.name + ".md")


def output_is_inside_input(input_root: Path, output_root: Path) -> bool:
    """Detect the 'output nested inside input' footgun before walking."""
    try:
        output_root.resolve().relative_to(input_root.resolve())
    except ValueError:
        return False
    return True
