"""
CPCTF - Bitwise Scrumble

每个十进制数字与 key 数字独立进行 bitwise 运算。写出单 bit 真值表后可知，
附件中的三种表达式都等价于 `digit ^ key_digit`，所以密文 hex nibble 再异或
同一个 key digit 就能还原原始十进制数字串。
"""

from __future__ import annotations


KEY = "0123456789012109876543210"
ENCRYPTED_FLAG = "10aa77170b38758c146245779086332e5e8237430f362d317310124333b999b890043152135"


def long_to_bytes(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def recover_decimal_digits(part: str) -> str:
    digits = []
    for encrypted_nibble, key_digit in zip(part, KEY):
        digits.append(str(int(encrypted_nibble, 16) ^ int(key_digit)))
    return "".join(digits)


def solve() -> str:
    parts = (
        ENCRYPTED_FLAG[:25],
        ENCRYPTED_FLAG[25:50],
        ENCRYPTED_FLAG[50:75],
    )
    decimal_text = "".join(recover_decimal_digits(part) for part in parts)
    return long_to_bytes(int(decimal_text)).decode()


def main() -> None:
    print(solve())


if __name__ == "__main__":
    main()
