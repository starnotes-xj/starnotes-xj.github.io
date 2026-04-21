#!/usr/bin/env python3
"""
题目名称: Ancient Spell (SSTV)
类别: Misc (摩尔斯电码变体解码)
解题思路:
    1. 音频中包含自定义摩尔斯电码变体
    2. "bi" 对应点 "."，"bo" 对应划 "-"
    3. 按空格分割单词，逐个解码摩尔斯字符
    4. 从标准输入读取解码后的文本
"""

import sys

# 标准摩尔斯电码映射表
MORSE_MAP = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z", "-----": "0", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9",
}


def decode_word(w: str) -> str:
    """将 bi/bo 编码的单词解码为摩尔斯字符"""
    parts = []
    i = 0
    while i < len(w):
        if w.startswith("bi", i):
            parts.append(".")
            i += 2
            continue
        if w.startswith("bo", i):
            parts.append("-")
            i += 2
            continue
        i += 1
    morse = "".join(parts)
    return MORSE_MAP.get(morse, "?")


def decode_line(line: str) -> str:
    """解码一行 bi/bo 编码的文本"""
    words = line.strip().split()
    return "".join(decode_word(w) for w in words)


def main():
    """从标准输入或文件读取并解码"""
    if len(sys.argv) > 1:
        # 从文件读取
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        print(decode_line(line))
        except OSError as e:
            print(f"[!] 无法读取文件: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 从标准输入读取
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            print(decode_line(line))


if __name__ == "__main__":
    main()
