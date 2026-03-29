#!/usr/bin/env python3
"""
题目名称: Novruz Reverse by Zoktay (基础版)
类别: Reverse Engineering (逆向工程 - 字符串标记验证)
解题思路:
    1. 在二进制文件中搜索关键字符串标记
    2. 验证 NovruzCT、Masalli、xeberdar、2025 是否存在
    3. 组合得到 flag: NovruzCTF{21_Masalli_xeberdar2025}
"""

import sys

# 需要在二进制中存在的关键标记
MARKERS = [b"NovruzCT", b"Masalli", b"xeberdar", b"2025"]
# 最终 flag
FLAG = "NovruzCTF{21_Masalli_xeberdar2025}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "novruz_rev_zoktay"

    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"[!] 无法读取文件: {e}", file=sys.stderr)
        sys.exit(1)

    # 验证关键标记
    missing = [m for m in MARKERS if m not in data]
    if missing:
        for m in missing:
            print(f"[!] 未发现关键标记: {m.decode('ascii', 'ignore')}")
        sys.exit(1)

    print(f"[+] 所有标记验证通过")
    print(FLAG)


if __name__ == "__main__":
    main()
