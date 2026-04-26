from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MirrorConfig:
    input_dir: Path
    output_dir: Path | None = None
    bundle_path: Path | None = None
    to_stdout: bool = False
    overwrite: bool = False
    dry_run: bool = False
    workers: int = 1
    skip_patterns: tuple[str, ...] = ()
    include_hidden: bool = False
    follow_symlinks: bool = False
    use_default_ignore: bool = True
    use_gitignore: bool = True
    add_frontmatter: bool = True
    fence_code: bool = True
    quiet: bool = False
    verbose: bool = False


@dataclass(frozen=True)
class ConversionResult:
    """Outcome of converting one file. Never raises into the caller."""

    src: Path
    rel: Path
    status: str  # "ok" | "skipped" | "empty" | "failed"
    content: str = ""
    message: str = ""


@dataclass
class RunSummary:
    converted: int = 0
    skipped: int = 0
    empty: int = 0
    failed: int = 0
    bytes_in: int = 0
    chars_out: int = 0
    token_count: int = 0
    failures: list[tuple[Path, str]] = field(default_factory=list)

    def add(self, result: ConversionResult, src_size: int) -> None:
        self.bytes_in += src_size
        self.chars_out += len(result.content)
        if result.status == "ok":
            self.converted += 1
        elif result.status == "skipped":
            self.skipped += 1
        elif result.status == "empty":
            self.empty += 1
        else:
            self.failed += 1
            self.failures.append((result.src, result.message))
