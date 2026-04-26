from __future__ import annotations

import logging
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from mdmirror.bundle import render_tree, write_bundle, write_bundle_to
from mdmirror.config import ConversionResult, MirrorConfig, RunSummary
from mdmirror.converter import convert_file
from mdmirror.ignore import build_spec, load_gitignore
from mdmirror.mirror import to_output_path
from mdmirror.tokens import count_tokens
from mdmirror.walker import walk_files

log = logging.getLogger("mdmirror")


def run(config: MirrorConfig) -> RunSummary:
    summary = RunSummary()
    spec = build_spec(
        use_default=config.use_default_ignore,
        use_gitignore_spec=load_gitignore(config.input_dir) if config.use_gitignore else None,
        extra_patterns=config.skip_patterns,
    )
    files = list(
        walk_files(
            config.input_dir,
            spec=spec,
            include_hidden=config.include_hidden,
            follow_symlinks=config.follow_symlinks,
        )
    )
    log.info("discovered %d files under %s", len(files), config.input_dir)

    if config.dry_run:
        for src in files:
            if config.output_dir is not None:
                dst = to_output_path(src, config.input_dir, config.output_dir)
                log.info("[dry-run] %s -> %s", src, dst)
            else:
                log.info("[dry-run] would convert %s", src)
        if config.bundle_path is not None:
            log.info("[dry-run] would write bundle: %s", config.bundle_path)
        if config.to_stdout:
            log.info("[dry-run] would stream bundle to stdout")
        return summary

    results = _convert_all(files, config, summary)
    results.sort(key=lambda r: r.rel.as_posix())

    summary.token_count = _compute_token_count(results)

    if config.to_stdout:
        tree = render_tree(files, config.input_dir)
        write_bundle_to(sys.stdout, results, input_root=config.input_dir, tree_summary=tree)
        log.info("bundle streamed to stdout")
    elif config.bundle_path is not None:
        tree = render_tree(files, config.input_dir)
        write_bundle(
            config.bundle_path,
            results,
            input_root=config.input_dir,
            tree_summary=tree,
        )
        log.info("bundle written: %s", config.bundle_path)
    return summary


def _convert_all(
    files: list[Path],
    config: MirrorConfig,
    summary: RunSummary,
) -> list[ConversionResult]:
    results: list[ConversionResult] = []
    if config.workers <= 1:
        for src in files:
            results.append(_handle_one(src, config, summary))
        return results

    with ProcessPoolExecutor(max_workers=config.workers) as pool:
        futures = {pool.submit(convert_file, src, config): src for src in files}
        for future in as_completed(futures):
            src = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                rel = src.relative_to(config.input_dir)
                result = ConversionResult(src=src, rel=rel, status="failed", message=str(exc))
            _record(src, result, config, summary)
            results.append(result)
    return results


def _handle_one(src: Path, config: MirrorConfig, summary: RunSummary) -> ConversionResult:
    result = convert_file(src, config)
    _record(src, result, config, summary)
    return result


def _record(
    src: Path,
    result: ConversionResult,
    config: MirrorConfig,
    summary: RunSummary,
) -> None:
    try:
        size = src.stat().st_size
    except OSError:
        size = 0
    summary.add(result, size)

    if result.status == "skipped":
        log.debug("skipped %s: %s", result.rel, result.message)
        return
    if result.status == "failed":
        log.warning("failed %s: %s", result.rel, result.message)
        return
    if result.status == "empty":
        log.warning("empty output for %s", result.rel)

    if config.output_dir is None or not result.content:
        return
    dst = to_output_path(src, config.input_dir, config.output_dir)
    if dst.exists() and not config.overwrite:
        log.debug("skip-existing %s", dst)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(result.content, encoding="utf-8", newline="\n")
    log.debug("wrote %s", dst)


def _compute_token_count(results: list[ConversionResult]) -> int:
    parts = [r.content for r in results if r.status in ("ok", "empty") and r.content]
    if not parts:
        return 0
    return count_tokens("".join(parts))
