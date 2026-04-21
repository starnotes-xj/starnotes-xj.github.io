"""
CPCTF - mirage

这题的核心不是后端校验，也不是复制事件拦截，而是前端把真实字符串交给 DOM，
再用自定义字体把字符外观伪装成另一套“看起来像 flag 的东西”。

复现方式：
1. 抓取首页 HTML。
2. 直接在源码里搜索 `CPCTF{`。
3. 提取唯一真实 flag 并输出。
"""

from __future__ import annotations

import re
import urllib.request


URL = "https://mirage.web.cpctf.space/"
FLAG_PATTERN = re.compile(r"CPCTF\{[^}\r\n]+\}")


def fetch_html(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_flag(html: str) -> str:
    matches = FLAG_PATTERN.findall(html)
    unique = []
    for match in matches:
        if match not in unique:
            unique.append(match)
    if len(unique) != 1:
        raise RuntimeError(f"expected exactly one CPCTF flag in source, got {unique}")
    return unique[0]


def main() -> None:
    html = fetch_html(URL)
    flag = extract_flag(html)
    print(flag)


if __name__ == "__main__":
    main()
