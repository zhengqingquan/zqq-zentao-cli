#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""python -m zqq_zentao_cli"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
