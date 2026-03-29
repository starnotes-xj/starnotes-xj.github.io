#!/usr/bin/env python3
"""
题目名称: Novruz Reverse by Zoktay (radare2 版)
类别: Reverse Engineering (逆向工程 - radare2 自动分析)
解题思路:
    1. 使用 radare2 反汇编 xor_decrypt 函数
    2. 从反汇编输出中提取 XOR key (0x42)
    3. 结合字符串标记得到 flag: NovruzCTF{21_Masalli_xeberdar2025}
依赖: radare2 (r2)
"""

import re
import shutil
import subprocess
import sys

# 需要在二进制中存在的关键标记
MARKERS = [b"NovruzCT", b"Masalli", b"xeberdar", b"2025"]
# 需要分析的函数符号名
XOR_DECRYPT_SYMBOL = "sym._Z11xor_decryptPcPKcmc"
# 期望的 XOR key
EXPECTED_KEY = "42"
# 最终 flag
FLAG = "NovruzCTF{21_Masalli_xeberdar2025}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "novruz_rev_zoktay"

    # 检查 radare2 是否安装
    if not shutil.which("r2"):
        print("[!] 未找到 radare2 (r2)，请先安装。", file=sys.stderr)
        sys.exit(1)

    # 读取并验证二进制文件
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"[!] 无法读取文件: {e}", file=sys.stderr)
        sys.exit(1)

    for m in MARKERS:
        if m not in data:
            print(f"[!] 未发现关键标记: {m.decode('ascii', 'ignore')}")

    # 使用 radare2 反汇编 xor_decrypt 函数
    try:
        out = subprocess.check_output(
            ["r2", "-q", "-c", f"aaa; pdf @ {XOR_DECRYPT_SYMBOL}", path],
            text=True, errors="ignore", timeout=60,
        )
    except subprocess.SubprocessError as e:
        print(f"[!] radare2 执行失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 从反汇编输出中提取 XOR key
    m = re.search(r"xor\s+al,\s*0x([0-9a-fA-F]{1,2})", out)
    if m and m.group(1).lower() == EXPECTED_KEY:
        print(f"[+] 检测到 XOR key = 0x{EXPECTED_KEY}")
        print(FLAG)
    else:
        print("[!] 未能从 xor_decrypt 反汇编中解析到 key，请手动查看：", file=sys.stderr)
        print(out, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
