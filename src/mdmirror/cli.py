from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from mdmirror import __version__
from mdmirror.config import MirrorConfig, RunSummary
from mdmirror.logging_setup import configure
from mdmirror.mirror import output_is_inside_input
from mdmirror.runner import run


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = _resolve_config(args)
    except _CLIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    log = configure(quiet=args.quiet, verbose=args.verbose)
    log.debug("config: %s", config)

    summary = run(config)
    _print_summary(summary, config, log)
    return 1 if summary.failed else 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mdmirror",
        description=(
            "Convert a folder into Claude-optimal Markdown context. "
            "Default: writes ./<input>.claude.md, a single paste-ready bundle. "
            "Use --tree to mirror as a folder of .md files instead."
        ),
        epilog=(
            "examples:\n"
            "  mdmirror repo                  # -> ./repo.claude.md\n"
            "  mdmirror repo --stdout | pbcopy  # paste-ready clipboard\n"
            "  mdmirror repo --tree           # -> ./repo_md/ (one .md per file)\n"
            "  mdmirror repo out --tree       # -> ./out/\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input_dir", type=Path, help="folder to convert")
    p.add_argument(
        "output",
        type=Path,
        nargs="?",
        default=None,
        help="bundle file (default mode) or tree dir (with --tree)",
    )
    p.add_argument(
        "--tree", action="store_true", help="mirror as a folder of .md files instead of one bundle"
    )
    p.add_argument(
        "--bundle",
        action="store_true",
        help="with --tree, also emit a bundle at ./<input>.claude.md",
    )
    p.add_argument(
        "--stdout", action="store_true", help="stream the bundle to stdout (great for `| pbcopy`)"
    )
    p.add_argument("--overwrite", action="store_true", help="overwrite existing output files")
    p.add_argument("--dry-run", action="store_true", help="report planned actions, write nothing")
    p.add_argument("--workers", type=int, default=1, help="parallel worker processes (default: 1)")
    p.add_argument(
        "--skip-pattern",
        action="append",
        default=[],
        metavar="PAT",
        help="extra gitignore-style pattern to skip (repeatable)",
    )
    p.add_argument(
        "--include-hidden", action="store_true", help="don't skip dotfiles / dotdirs by default"
    )
    p.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="follow symlinks (off by default; cycles detected)",
    )
    p.add_argument(
        "--no-default-ignore", action="store_true", help="don't apply the built-in skip list"
    )
    p.add_argument(
        "--no-gitignore", action="store_true", help="don't honor a .gitignore at the input root"
    )
    p.add_argument(
        "--no-frontmatter", action="store_true", help="don't add YAML frontmatter to each file"
    )
    p.add_argument(
        "--no-fence",
        action="store_true",
        help="don't fence source code (let markitdown handle everything)",
    )
    p.add_argument("-q", "--quiet", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"mdmirror {__version__}")
    return p


class _CLIError(ValueError):
    pass


def _resolve_config(args: argparse.Namespace) -> MirrorConfig:
    input_dir: Path = args.input_dir.expanduser().resolve()
    if not input_dir.is_dir():
        raise _CLIError(f"input directory does not exist: {input_dir}")

    to_stdout = args.stdout
    output_dir: Path | None = None
    bundle_path: Path | None = None

    if args.tree:
        # Tree mode: positional output is the tree dir; default to <input>_md.
        if to_stdout:
            raise _CLIError("--stdout writes a single bundle and is incompatible with --tree")
        output_dir = (
            args.output.expanduser().resolve()
            if args.output is not None
            else input_dir.parent / f"{input_dir.name}_md"
        )
        if args.bundle:
            bundle_path = Path.cwd() / f"{input_dir.name}.claude.md"
    else:
        # Default mode: bundle. Positional output is the bundle file.
        if to_stdout:
            if args.output is not None:
                raise _CLIError("--stdout writes to stdout; do not pass an output path")
        elif args.output is not None:
            bundle_path = args.output.expanduser().resolve()
        else:
            bundle_path = Path.cwd() / f"{input_dir.name}.claude.md"

    if output_dir is not None and output_is_inside_input(input_dir, output_dir):
        raise _CLIError(
            f"output dir {output_dir} is inside input dir {input_dir}; "
            "would recurse into its own output"
        )
    if bundle_path is not None and output_is_inside_input(input_dir, bundle_path.parent):
        raise _CLIError(
            f"bundle path {bundle_path} is inside input dir {input_dir}; "
            "move it elsewhere or add it to --skip-pattern"
        )

    quiet = args.quiet or to_stdout  # don't pollute pipes with INFO logs
    return MirrorConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        bundle_path=bundle_path,
        to_stdout=to_stdout,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        workers=max(1, args.workers),
        skip_patterns=tuple(args.skip_pattern),
        include_hidden=args.include_hidden,
        follow_symlinks=args.follow_symlinks,
        use_default_ignore=not args.no_default_ignore,
        use_gitignore=not args.no_gitignore,
        add_frontmatter=not args.no_frontmatter,
        fence_code=not args.no_fence,
        quiet=quiet,
        verbose=args.verbose,
    )


def _print_summary(summary: RunSummary, config: MirrorConfig, log: logging.Logger) -> None:
    log.info(
        "done: %d converted, %d skipped, %d empty, %d failed | "
        "%.1f KB in -> %.1f KB md (%s tokens)",
        summary.converted,
        summary.skipped,
        summary.empty,
        summary.failed,
        summary.bytes_in / 1024,
        summary.chars_out / 1024,
        f"{summary.token_count:,}",
    )
    for path, msg in summary.failures[:10]:
        log.info("  failed: %s — %s", path, msg)
    if len(summary.failures) > 10:
        log.info("  ... and %d more failures", len(summary.failures) - 10)
