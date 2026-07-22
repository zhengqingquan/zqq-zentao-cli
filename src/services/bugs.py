#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bug operations via ZenTaoClient."""

from __future__ import annotations

from typing import Any

from ..protocol import ZenTaoClient


def my_bugs(client: ZenTaoClient) -> list[dict[str, Any]]:
    return client.my_bugs()
