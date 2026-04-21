"""
CPCTF - Sign up for traP

判定输入字符串是否满足 traQ ID 规则：
- 长度 1..32
- 只能包含英文字母、数字、下划线和连字符
- 首尾字符不能是下划线或连字符

本解法用一个正则表达式同时约束字符集、长度和首尾字符。
"""

from __future__ import annotations

import re
import sys


TRAQ_ID_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,30}[A-Za-z0-9])?$")


def is_valid_traq_id(text: str) -> bool:
    return TRAQ_ID_PATTERN.fullmatch(text) is not None


def main() -> None:
    s = sys.stdin.readline().rstrip("\n")
    print(200 if is_valid_traq_id(s) else 400)


if __name__ == "__main__":
    main()
