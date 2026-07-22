#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive write confirmation (skip with --yes)."""

from __future__ import annotations

import sys


def confirm_or_exit(message: str, *, yes: bool = False) -> None:
    """Ask for confirmation on stderr; exit 1 if declined.

    With ``yes=True`` (CLI ``--yes``), skip the prompt.
    Non-interactive stdin (no TTY) without ``--yes`` aborts.
    """
    if yes:
        return
    if not sys.stdin.isatty():
        raise SystemExit(
            f"{message}\nRefusing write without --yes (stdin is not a TTY)."
        )
    print(message, file=sys.stderr)
    try:
        answer = input("Proceed? [y/N] ").strip().lower()
    except EOFError:
        raise SystemExit("Aborted.") from None
    if answer not in ("y", "yes"):
        raise SystemExit("Aborted.")
