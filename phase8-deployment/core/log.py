"""Logging helper for Phase 8 Government Biz.

Provides a preconfigured logger with a sensible format.  Use
``get_logger(__name__)`` to obtain a module‑specific logger.
"""

import logging
import sys


def _configure_root_logger() -> None:
    if len(logging.root.handlers) > 0:
        # Already configured
        return
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name, configuring the root logger on first use."""
    _configure_root_logger()
    return logging.getLogger(name)
