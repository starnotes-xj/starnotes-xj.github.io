"""
CPCTF - Dualcast

题目脚本只做了一件事：把 flag.encode() 用 bytes_to_long 转成十进制整数。
因此解题过程就是读取归档后的 out.txt，提取 c，并把它按大端序转回字节串。
"""

from pathlib import Path
import re


def extract_decimal_value(text: str) -> int:
    """从 `c = 12345` 这种输出里提取十进制整数。"""
    match = re.search(r"c\s*=\s*(\d+)", text)
    if match is None:
        raise ValueError("未在 out.txt 中找到形如 `c = <整数>` 的输出")
    return int(match.group(1))


def int_to_bytes(value: int) -> bytes:
    """把大整数按大端序还原为原始字节串。"""
    if value < 0:
        raise ValueError("只支持非负整数")
    if value == 0:
        return b"\x00"
    length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "big")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    out_path = base_dir / "files" / "Dualcast" / "out.txt"

    raw_text = out_path.read_text(encoding="utf-8")
    c = extract_decimal_value(raw_text)
    flag = int_to_bytes(c).decode("utf-8")

    print(flag)


if __name__ == "__main__":
    main()
