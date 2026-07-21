#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cookie HTTP session and web login."""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..config import USER_AGENT, md5_hex


class Session:
    def __init__(self, server: str, insecure: bool = True):
        self.server = server.rstrip("/")
        self.cookies: dict[str, str] = {}
        self.insecure = insecure
        self._ssl = ssl._create_unverified_context() if insecure else None

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def _merge_set_cookie(self, headers: Any) -> None:
        raw_list: list[str] = []
        if hasattr(headers, "get_all"):
            raw_list = headers.get_all("Set-Cookie") or []
        elif "Set-Cookie" in headers:
            raw_list = [headers["Set-Cookie"]]
        for raw in raw_list:
            nv = str(raw).split(";", 1)[0]
            if "=" in nv:
                k, v = nv.split("=", 1)
                self.cookies[k.strip()] = v.strip()

    def request(
        self,
        method: str,
        path: str,
        *,
        form: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        modal: bool = False,
    ) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{self.server}/{path.lstrip('/')}"
        hdrs = {
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.server}/",
        }
        if self.cookies:
            hdrs["Cookie"] = self._cookie_header()
        if modal:
            hdrs["X-Zui-Modal"] = "true"
        if headers:
            hdrs.update(headers)

        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            hdrs["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        req = urllib.request.Request(url, data=data, headers=hdrs, method=method.upper())
        try:
            with urllib.request.urlopen(req, context=self._ssl, timeout=60) as res:
                body = res.read()
                self._merge_set_cookie(res.headers)
                status = res.status
                ctype = res.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
            self._merge_set_cookie(e.headers)
            status = e.code
            ctype = e.headers.get("Content-Type", "") if e.headers else ""

        text = body.decode("utf-8", errors="replace")
        parsed: Any = text
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass
        return {
            "ok": 200 <= status < 300,
            "status": status,
            "data": parsed,
            "raw": text,
            "content_type": ctype,
        }

    def login(self, account: str, password: str) -> None:
        rand = self.request("GET", "/user-refreshRandom.html")
        verify = str(rand["data"] if isinstance(rand["data"], str) else rand["raw"]).strip()
        if not re.fullmatch(r"\d+", verify):
            raise SystemExit(f"refreshRandom unexpected: {verify[:80]}")
        hashed = md5_hex(md5_hex(password) + verify)
        r = self.request(
            "POST",
            "/user-login.html",
            form={
                "account": account,
                "password": hashed,
                "passwordStrength": "1",
                "referer": "/",
                "verifyRand": verify,
                "keepLogin": "1",
                "captcha": "",
            },
            headers={"Referer": f"{self.server}/user-login.html"},
        )
        data = r["data"]
        ok_json = isinstance(data, dict) and (
            data.get("result") == "success" or data.get("status") == "success"
        )
        has_session = bool(
            self.cookies.get("zentaosid")
            and (self.cookies.get("za") or self.cookies.get("zp") or self.cookies.get("keepLogin"))
        )
        if not ok_json and not has_session:
            raise SystemExit(
                f"Web login failed HTTP {r['status']}: {r['raw'][:120]}. Check ZENTAO_PASSWORD."
            )
        if not self.cookies.get("zentaosid"):
            raise SystemExit("Login succeeded but zentaosid cookie is missing")
        print(f"auth: web-login(account={account})", file=sys.stderr)
