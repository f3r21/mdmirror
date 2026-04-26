from __future__ import annotations

import logging
import sys


def configure(*, quiet: bool, verbose: bool) -> logging.Logger:
    if quiet and verbose:
        raise ValueError("--quiet and --verbose are mutually exclusive")
    level = logging.WARNING if quiet else logging.DEBUG if verbose else logging.INFO

    logger = logging.getLogger("mdmirror")
    logger.handlers.clear()
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
