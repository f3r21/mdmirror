# mdmirror

[![PyPI version](https://img.shields.io/pypi/v/mdmirror.svg)](https://pypi.org/project/mdmirror/)
[![CI](https://github.com/f3r21/mdmirror/actions/workflows/ci.yml/badge.svg)](https://github.com/f3r21/mdmirror/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/mdmirror.svg)](https://pypi.org/project/mdmirror/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Turn any folder into Claude-optimal Markdown context with one command.

```bash
mdmirror repo                  # → ./repo.claude.md
mdmirror repo --stdout | pbcopy  # paste-ready clipboard
```

## What it does

- Recursively walks a folder.
- Converts office docs / PDFs / HTML via [markitdown](https://github.com/microsoft/markitdown).
- Source code (`.py`, `.ts`, `.go`, …) is fenced with the right language tag — no mangling.
- Each file gets a `source:` frontmatter so the LLM always knows where a chunk came from.
- Output is sorted by path: deterministic, diffable across runs.
- Token count is exact (via `tiktoken`), not a heuristic.
- Aggressive default ignore list: `.git`, `node_modules`, `dist`, lockfiles, fonts, images, archives. Honors `.gitignore`.

## Install

```bash
pipx install mdmirror     # recommended — isolated env
# or
uv tool install mdmirror
# or
pip install mdmirror
```

Office formats (docx, xlsx, pptx, pdf, outlook) ship in the base install. For audio transcription via whisper:

```bash
pipx install '.[audio]'   # adds whisper, youtube-transcription
pipx install '.[all]'     # everything
```

## Modes

### Default — Claude bundle

```bash
mdmirror repo                # → ./repo.claude.md
mdmirror repo bundle.md      # → ./bundle.md
mdmirror repo --stdout       # stream to stdout
```

The bundle is a single `.md` with a header, a complete file tree, then every file in alphabetical order:

````markdown
# Context bundle: repo

Source root: `/path/to/repo`

## File tree
```
README.md
src/lib/foo.ts
src/main.py
```

---
source: README.md
bytes: 312
---

# Hello

…

<!-- ────────────────────────────── -->

---
source: src/lib/foo.ts
bytes: 412
---

```ts
// file contents
```
````

### Tree mirror

For when you want one `.md` per file on disk:

```bash
mdmirror repo --tree           # → ./repo_md/
mdmirror repo out --tree       # → ./out/
mdmirror repo out --tree --bundle   # tree AND ./repo.claude.md
```

## Flags

| Flag | Purpose |
|------|---------|
| `--tree` | Mirror as a folder of `.md` files instead of one bundle |
| `--bundle` | With `--tree`, also emit a bundle at `./<input>.claude.md` |
| `--stdout` | Stream the bundle to stdout (great for `\| pbcopy`) |
| `--overwrite` | Replace existing output files |
| `--dry-run` | Report planned actions, write nothing |
| `--workers N` | Parallel worker processes |
| `--skip-pattern PAT` | Extra gitignore-style pattern (repeatable) |
| `--include-hidden` | Don't skip dotfiles / dotdirs |
| `--follow-symlinks` | Follow symlinks (cycle-safe) |
| `--no-default-ignore` | Disable the built-in skip list |
| `--no-gitignore` | Don't honor a root `.gitignore` |
| `--no-frontmatter` | Strip the `source:` YAML header |
| `--no-fence` | Disable code fencing (everything goes through markitdown) |
| `-q`, `-v` | Quiet / verbose logging |

## Behaviors worth knowing

- **Naming (tree mode):** `report.docx` becomes `report.docx.md` so a sibling `report.pdf` doesn't collide. `*.md` files pass through unchanged.
- **Output safety:** refuses to run if the output dir is inside the input dir.
- **Failures don't crash the run.** Each failed file is logged and counted; everything else still gets converted.
- **Logs go to stderr.** Stdout stays clean for `--stdout` piping.

## Develop

```bash
uv pip install -e '.[dev]'
.venv/bin/pytest -q -m "not integration"   # fast (~0.5s)
.venv/bin/pytest -q                         # incl. real markitdown roundtrip
```
