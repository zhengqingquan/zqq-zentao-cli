#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZenTao dual-backend CLI (Web PATHINFO / REST Token).

Auth:
  - zqq-zentao login -s <url> -u <account> -p <password>
  - Or env ZENTAO_SERVER/ZENTAO_URL, ZENTAO_ACCOUNT, ZENTAO_PASSWORD / ZENTAO_TOKEN
  - Caches webCookies + token in ~/.config/zentao/zentao.json (no password on disk)
  - Backend: --backend / ZENTAO_BACKEND = web|rest|auto
  - TLS: --insecure / --secure / ZENTAO_INSECURE (default skip verify)
  - Global (aligned with official zentao-cli):
      -V/--version-flag, --format, --silent, --timeout, --config, --machine-readable
      --pick <fields> for table column selection

Never print Cookie / password / Token.

Implementation lives in ``cli_app``; this module is the console entry and test surface.
"""

from __future__ import annotations

from .cli_app.capability import capability as _capability
from .cli_app.dispatch import main
from .cli_app.fields import fields_for as _fields_for
from .cli_app.fields import parse_pick as _parse_pick
from .cli_app.parser import build_parser

__all__ = ["main", "build_parser", "_capability", "_fields_for", "_parse_pick"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
