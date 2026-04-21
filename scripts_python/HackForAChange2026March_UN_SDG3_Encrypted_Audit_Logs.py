#!/usr/bin/env python3
"""
HackForAChange 2026 March - UN SDG3 - Encrypted Audit Logs (Crypto)
XOR 重复密钥加密 + 已知明文攻击

攻击思路:
    1. 审计日志中的 token 使用 Base32 编码
    2. 第 108 行的 token 解码后是非 ASCII 数据 — 被 XOR 加密
    3. 日志第 62 行泄露了加密配置: XOR mode=repeating key_len=4
    4. Flag 格式 "SDG{" 恰好 4 字节 = 密钥长度, 已知明文攻击直接恢复密钥
"""

import base64
import re
import sys


def extract_tokens(log_text: str) -> list[tuple[int, str]]:
    """从审计日志中提取所有 Base32 编码的 token"""
    # 匹配日志中各种 token 字段
    patterns = [
        r'Token self-test:\s+([A-Z2-7=]+)',
        r'Snapshot token:\s+([A-Z2-7=]+)',
        r'EncryptedToken:\s+([A-Z2-7=]+)',
        r'Key rotation token:\s+([A-Z2-7=]+)',
    ]
    tokens = []
    for i, line in enumerate(log_text.splitlines(), 1):
        for pat in patterns:
            m = re.search(pat, line)
            if m:
                tokens.append((i, m.group(1)))
    return tokens


def xor_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """使用重复密钥 XOR 解密"""
    return bytes([ciphertext[i] ^ key[i % len(key)] for i in range(len(ciphertext))])


def recover_key(ciphertext: bytes, known_plaintext: bytes) -> bytes:
    """已知明文攻击: 从密文和已知明文恢复 XOR 密钥"""
    return bytes([ciphertext[i] ^ known_plaintext[i] for i in range(len(known_plaintext))])


def solve(log_path: str = None):
    """主求解函数"""
    print("=" * 60)
    print("Encrypted Audit Logs — XOR Known-Plaintext Attack")
    print("=" * 60)

    # 如果提供了日志文件路径, 从文件提取 token
    if log_path:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_text = f.read()
        tokens = extract_tokens(log_text)
        print(f"\n提取到 {len(tokens)} 个 token:")
        for line_no, tok in tokens:
            raw = base64.b32decode(tok)
            try:
                text = raw.decode('ascii')
                print(f"  L{line_no:3d}: {text}")
            except UnicodeDecodeError:
                print(f"  L{line_no:3d}: [NON-ASCII] {raw.hex()}")
    else:
        print("\n未提供日志文件, 直接使用已知的加密 token")

    # 第 108 行的加密 token (Base32 编码)
    encrypted_b32 = "LHHPPHR25OEII2F22XIG7OWS2IZ3FVWTNS7YTAB65DJNKPV42XKW72EH2R3Q===="

    # Step 1: Base32 解码
    ciphertext = base64.b32decode(encrypted_b32)
    print(f"\n[Step 1] Base32 解码")
    print(f"  密文 hex: {ciphertext.hex()}")
    print(f"  密文长度: {len(ciphertext)} bytes")

    # Step 2: 已知明文攻击恢复密钥
    # 日志第 62 行: Cipher config: XOR mode=repeating key_len=4
    # Flag 格式: SDG{...}, 前 4 字节 = 密钥长度
    known_pt = b"SDG{"
    key = recover_key(ciphertext, known_pt)
    print(f"\n[Step 2] 已知明文攻击")
    print(f"  已知明文: {known_pt}")
    print(f"  恢复密钥: 0x{key.hex()} ({list(key)})")

    # Step 3: 解密
    plaintext = xor_decrypt(ciphertext, key)
    flag = plaintext.decode('ascii')
    print(f"\n[Step 3] XOR 解密")
    print(f"  Flag: {flag}")

    # 验证: flag 以 SDG{ 开头, 以 } 结尾
    assert flag.startswith("SDG{") and flag.endswith("}"), "Flag 格式验证失败!"
    print(f"  格式验证: PASS")


if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else None
    solve(log_path)
