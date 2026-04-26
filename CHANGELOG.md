# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-04-26

### Added
- **Default mode is now Claude bundle.** `mdmirror <input>` writes a single paste-ready `<input>.claude.md` with no flags required.
- `--stdout` flag for piping the bundle straight to clipboard (`mdmirror repo --stdout | pbcopy`).
- `--tree` flag to opt back into the folder-of-`.md`-files mirror.
- Exact token counting via `tiktoken` (o200k_base encoding) — no more `chars/4` heuristic.
- Real-markitdown integration test against a committed `.docx` fixture.
- Bundle output is sorted by relative path — deterministic and diffable across runs.
- Office formats (`docx`, `xlsx`, `pptx`, `pdf`, `outlook`) are pulled in as base dependencies.

### Changed
- Default ignore list now also skips fonts, images, snapshots, vendored content (previously gated behind a `-c` preset).
- `--workers N` parallel mode is now covered by tests; output is byte-identical to sequential mode.

### Removed
- `-c` / `--claude` flag (Claude bundle is the default; the flag is no longer needed).

## [0.1.0] — initial development

- Initial scaffold: recursive folder walker, markitdown converter, tree-mirror writer, CLI entry point.
