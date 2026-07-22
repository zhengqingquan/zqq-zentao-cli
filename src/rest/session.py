#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REST Token HTTP session."""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..config import USER_AGENT, resolve_password, resolve_token


class RestSession:
    def __init__(
        self,
        server: str,
        insecure: bool = True,
        *,
        account: str = "",
        timeout: float = 60.0,
    ):
        self.server = server.rstrip("/")
        self.account = account
        self.token = ""
        self.insecure = insecure
        self.timeout = timeout
        self._ssl = ssl._create_unverified_context() if insecure else None

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        p = path if path.startswith("/") else f"/{path}"
        if p.startswith("/api.php"):
            return f"{self.server}{p}"
        return f"{self.server}/api.php/v1{p}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        url = self._url(path)
        if query:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)

        hdrs = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if auth and self.token:
            hdrs["Token"] = self.token
        if headers:
            hdrs.update(headers)

        data = None
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=hdrs, method=method.upper())
        try:
            with urllib.request.urlopen(req, context=self._ssl, timeout=self.timeout) as res:
                body = res.read()
                status = res.status
                ctype = res.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            body = e.read() if e.fp else b""
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

    def login(
        self,
        account: str,
        password: str | None = None,
        *,
        prefer_stored: bool = True,
        force_password: bool = False,
    ) -> str:
        """
        Authenticate. Returns the token in use.
        prefer_stored: try env/profile token before password exchange.
        force_password: always exchange password (used by `zqq-zentao login`).
        """
        self.account = account
        if not force_password and prefer_stored:
            token = resolve_token(server=self.server, account=account)
            if token:
                self.token = token
                print(f"auth: rest-token(account={account})", file=sys.stderr)
                return self.token

        pwd = password if password is not None else resolve_password()
        r = self.request(
            "POST",
            "/tokens",
            json_body={"account": account, "password": pwd},
            auth=False,
        )
        data = r["data"]
        if not isinstance(data, dict) or not data.get("token"):
            raise SystemExit(
                f"REST login failed HTTP {r['status']}: {r['raw'][:160]}. "
                "Check password / ZENTAO_PASSWORD or set ZENTAO_TOKEN."
            )
        self.token = str(data["token"])
        print(f"auth: rest-login(account={account})", file=sys.stderr)
        return self.token
