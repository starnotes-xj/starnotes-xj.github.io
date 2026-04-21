#!/usr/bin/env python3
"""
ACSC Qualification 2026 - Dino Vault

离线求解脚本：输入同一只恐龙（例如 Vexillum Rex）在同一连接中
两次下载得到的 (ciphertext, modulus)，利用共享素因子攻击恢复原文。

判断 RSA 的关键线索来自附件 app.py：
1. modulus = transmission_key * vault_key（两个大素数相乘）
2. exponent = 2**16 + 1 = 65537
3. ciphertext = pow(message, exponent, modulus)

这就是 textbook RSA。
"""

from __future__ import annotations

import argparse
import math
import re
import sys

from Crypto.Util.number import inverse, long_to_bytes

PUBLIC_EXPONENT = 65537
DNA_LOOKUP = {"A": 0, "T": 1, "G": 2, "C": 3}


def from_dna(dna: str) -> str:
    """把题目中的 DNA 字符串逆回普通文本。"""
    if len(dna) % 4 != 0:
        raise ValueError("DNA 长度不是 4 的倍数，无法按题目编码规则还原")

    chars: list[str] = []
    for i in range(0, len(dna), 4):
        value = 0
        for j, base in enumerate(dna[i : i + 4]):
            value |= DNA_LOOKUP[base] << (2 * j)
        chars.append(chr(value))
    return "".join(chars)


def solve(ciphertext1: str, modulus1: str, ciphertext2: str, modulus2: str) -> tuple[int, str, str | None]:
    """执行共享素因子攻击并返回 (shared_prime, plaintext, flag)。"""
    c1 = int(ciphertext1, 16)
    n1 = int(modulus1)
    n2 = int(modulus2)

    shared_prime = math.gcd(n1, n2)
    if shared_prime in (1, n1, n2):
        raise ValueError("两组模数没有得到有效共享质因子，请确认它们来自同一只恐龙的同一连接")

    q1 = n1 // shared_prime
    phi = (shared_prime - 1) * (q1 - 1)
    private_exponent = inverse(PUBLIC_EXPONENT, phi)

    message_int = pow(c1, private_exponent, n1)
    dna = long_to_bytes(message_int).decode()
    plaintext = from_dna(dna)

    match = re.search(r"dach2026\{[^}]+\}", plaintext)
    flag = match.group(0) if match else None
    return shared_prime, plaintext, flag


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Solve ACSC Qualification 2026 Dino Vault from two modulus/ciphertext pairs")
    parser.add_argument("--ciphertext1", required=True, help="第一组十六进制密文")
    parser.add_argument("--modulus1", required=True, help="第一组十进制模数")
    parser.add_argument("--ciphertext2", required=True, help="第二组十六进制密文")
    parser.add_argument("--modulus2", required=True, help="第二组十进制模数")
    args = parser.parse_args()

    shared_prime, plaintext, flag = solve(args.ciphertext1, args.modulus1, args.ciphertext2, args.modulus2)

    print(f"[+] shared prime bits: {shared_prime.bit_length()}")
    print(f"[+] shared prime: {shared_prime}")
    print(f"[+] recovered plaintext: {plaintext}")
    if flag:
        print(f"[+] flag: {flag}")
    else:
        print("[!] 未在明文中自动匹配到 flag，请手动检查 recovered plaintext")


if __name__ == "__main__":
    main()
