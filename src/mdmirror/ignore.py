from __future__ import annotations

from pathlib import Path

import pathspec

DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = (
    # VCS
    ".git/",
    ".hg/",
    ".svn/",
    # OS / editors
    ".DS_Store",
    "Thumbs.db",
    ".idea/",
    ".vscode/",
    "*.swp",
    # Python
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "venv/",
    ".tox/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "*.egg-info/",
    # Node / web
    "node_modules/",
    ".next/",
    ".nuxt/",
    ".turbo/",
    ".cache/",
    ".parcel-cache/",
    "dist/",
    "build/",
    "out/",
    "coverage/",
    # Vendored / third-party
    "vendor/",
    "third_party/",
    "third-party/",
    # Lockfiles (rarely useful as LLM context, very large)
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "Gemfile.lock",
    "poetry.lock",
    "uv.lock",
    "composer.lock",
    "*.lock.json",
    # Compiled / minified
    "*.min.js",
    "*.min.css",
    "*.map",
    # Snapshots
    "*.snap",
    # Binaries / archives (markitdown won't help here)
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.7z",
    "*.rar",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.class",
    "*.jar",
    "*.o",
    "*.a",
    # Media / images / fonts (large, rarely useful in markdown form)
    "*.mp4",
    "*.mov",
    "*.webm",
    "*.mkv",
    "*.iso",
    "*.dmg",
    "*.svg",
    "*.ico",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.otf",
    "*.eot",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.webp",
    "*.heic",
    "*.bmp",
    "*.psd",
    # Mirror outputs (avoid converting yesterday's mirror)
    "*.claude.md",
)


def load_gitignore(input_root: Path) -> pathspec.PathSpec | None:
    gi = input_root / ".gitignore"
    if not gi.is_file():
        return None
    try:
        lines = gi.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    return pathspec.PathSpec.from_lines("gitignore", lines)


def build_spec(
    *,
    use_default: bool,
    use_gitignore_spec: pathspec.PathSpec | None,
    extra_patterns: tuple[str, ...],
) -> pathspec.PathSpec:
    patterns: list[str] = []
    if use_default:
        patterns.extend(DEFAULT_IGNORE_PATTERNS)
    patterns.extend(extra_patterns)
    spec = pathspec.PathSpec.from_lines("gitignore", patterns)
    if use_gitignore_spec is None:
        return spec
    return _MergedSpec(spec, use_gitignore_spec)


class _MergedSpec:
    """Two PathSpecs OR'd together. Either matching = ignored."""

    def __init__(self, a: pathspec.PathSpec, b: pathspec.PathSpec) -> None:
        self._a = a
        self._b = b

    def match_file(self, path: str) -> bool:
        return self._a.match_file(path) or self._b.match_file(path)


def is_hidden(name: str) -> bool:
    return name.startswith(".") and name not in (".", "..")
