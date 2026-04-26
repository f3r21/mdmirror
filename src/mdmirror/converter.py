from __future__ import annotations

from pathlib import Path

from mdmirror.config import ConversionResult, MirrorConfig
from mdmirror.mirror import PASSTHROUGH_SUFFIXES

# Extension -> language hint for fenced code blocks. If present here, the file
# is treated as text and fenced directly instead of being handed to markitdown
# (which is built for office docs / pdf / html, not source code).
CODE_LANGS: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "ts",
    ".tsx": "tsx",
    ".js": "js",
    ".jsx": "jsx",
    ".mjs": "js",
    ".cjs": "js",
    ".go": "go",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".java": "java",
    ".scala": "scala",
    ".rb": "ruby",
    ".php": "php",
    ".pl": "perl",
    ".pm": "perl",
    ".lua": "lua",
    ".r": "r",
    ".dart": "dart",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".h": "c",
    ".c": "c",
    ".m": "objc",
    ".mm": "objc",
    ".cs": "csharp",
    ".fs": "fsharp",
    ".vb": "vbnet",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "fish",
    ".ps1": "powershell",
    ".sql": "sql",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".jsonc": "json",
    ".json5": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".xml": "xml",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".proto": "protobuf",
    ".tf": "hcl",
    ".hcl": "hcl",
    ".dockerfile": "dockerfile",
    ".env": "bash",
}

PLAIN_TEXT_SUFFIXES = {".txt", ".log", ".csv", ".tsv"}

# Things markitdown is good at. We don't strictly enforce — anything not in
# CODE_LANGS / PLAIN_TEXT / PASSTHROUGH falls through to markitdown anyway.
DOC_SUFFIXES = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".html",
    ".htm",
    ".epub",
    ".rtf",
    ".odt",
    ".odp",
    ".ods",
}

MAX_INLINE_TEXT_BYTES = 5 * 1024 * 1024  # skip giant text files


def convert_file(src: Path, config: MirrorConfig) -> ConversionResult:
    """Convert one file to markdown text. Never raises into the caller."""
    rel = src.relative_to(config.input_dir)
    suffix = src.suffix.lower()

    try:
        if suffix in PASSTHROUGH_SUFFIXES:
            text = src.read_text(encoding="utf-8", errors="replace")
            return _ok(src, rel, _wrap(text, src, rel, config, fence=None))

        if suffix == ".dockerfile" or src.name.lower() == "dockerfile":
            text = _read_text_capped(src)
            return _ok(src, rel, _wrap(text, src, rel, config, fence="dockerfile"))

        if config.fence_code and suffix in CODE_LANGS:
            text = _read_text_capped(src)
            return _ok(src, rel, _wrap(text, src, rel, config, fence=CODE_LANGS[suffix]))

        if suffix in PLAIN_TEXT_SUFFIXES:
            text = _read_text_capped(src)
            return _ok(src, rel, _wrap(text, src, rel, config, fence=None))

        # Documents and unknown suffixes -> hand to markitdown.
        text = _markitdown_convert(src)
        if not text.strip():
            return ConversionResult(
                src=src,
                rel=rel,
                status="empty",
                content=_wrap("", src, rel, config, fence=None),
                message="markitdown produced empty output",
            )
        return _ok(src, rel, _wrap(text, src, rel, config, fence=None))

    except _SkipFile as exc:
        return ConversionResult(src=src, rel=rel, status="skipped", message=str(exc))
    except Exception as exc:  # noqa: BLE001 — converter must never crash the run
        return ConversionResult(
            src=src, rel=rel, status="failed", message=f"{type(exc).__name__}: {exc}"
        )


class _SkipFile(Exception):
    pass


def _ok(src: Path, rel: Path, content: str) -> ConversionResult:
    return ConversionResult(src=src, rel=rel, status="ok", content=content)


def _read_text_capped(src: Path) -> str:
    if src.stat().st_size > MAX_INLINE_TEXT_BYTES:
        raise _SkipFile(f"file exceeds {MAX_INLINE_TEXT_BYTES} bytes")
    return src.read_text(encoding="utf-8", errors="replace")


def _markitdown_convert(src: Path) -> str:
    # Imported lazily so unit tests can run without the heavy dep installed.
    from markitdown import MarkItDown  # type: ignore[import-not-found]

    md = MarkItDown()
    result = md.convert(str(src))
    return getattr(result, "text_content", "") or ""


def _wrap(body: str, src: Path, rel: Path, config: MirrorConfig, *, fence: str | None) -> str:
    parts: list[str] = []
    if config.add_frontmatter:
        parts.append(_frontmatter(rel, src))
    if fence is not None:
        parts.append(f"```{fence}\n{body.rstrip()}\n```\n")
    else:
        parts.append(body if body.endswith("\n") else body + "\n")
    return "".join(parts)


def _frontmatter(rel: Path, src: Path) -> str:
    posix = rel.as_posix()
    try:
        size = src.stat().st_size
    except OSError:
        size = 0
    return f"---\nsource: {posix}\nbytes: {size}\n---\n\n"
