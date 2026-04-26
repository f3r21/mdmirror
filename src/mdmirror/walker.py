from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pathspec

from mdmirror.ignore import _MergedSpec, is_hidden

Spec = pathspec.PathSpec | _MergedSpec


def walk_files(
    root: Path,
    *,
    spec: Spec,
    include_hidden: bool,
    follow_symlinks: bool,
) -> Iterator[Path]:
    """Yield absolute file paths under `root`, honoring ignore rules.

    Directory pruning happens before descending — anything matched by the
    spec or hidden (when not allowed) is not entered, which avoids walking
    into `node_modules` etc.
    """
    visited: set[tuple[int, int]] = set()
    yield from _walk(root, root, spec, include_hidden, follow_symlinks, visited)


def _walk(
    root: Path,
    current: Path,
    spec: Spec,
    include_hidden: bool,
    follow_symlinks: bool,
    visited: set[tuple[int, int]],
) -> Iterator[Path]:
    try:
        entries = list(os.scandir(current))
    except (PermissionError, FileNotFoundError):
        return
    entries.sort(key=lambda e: e.name)

    for entry in entries:
        name = entry.name
        if not include_hidden and is_hidden(name):
            continue

        try:
            is_dir = entry.is_dir(follow_symlinks=follow_symlinks)
        except OSError:
            continue

        path = Path(entry.path)
        rel = path.relative_to(root).as_posix()
        match_target = rel + "/" if is_dir else rel
        if spec.match_file(match_target):
            continue

        if is_dir:
            if entry.is_symlink() and not follow_symlinks:
                continue
            if follow_symlinks:
                try:
                    st = entry.stat(follow_symlinks=True)
                except OSError:
                    continue
                key = (st.st_dev, st.st_ino)
                if key in visited:
                    continue
                visited.add(key)
            yield from _walk(root, path, spec, include_hidden, follow_symlinks, visited)
            continue

        try:
            if not entry.is_file(follow_symlinks=follow_symlinks):
                continue
        except OSError:
            continue
        yield path
