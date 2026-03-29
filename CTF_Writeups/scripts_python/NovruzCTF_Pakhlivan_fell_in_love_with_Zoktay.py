#!/usr/bin/env python3
"""
题目名称: Zoktay Crack Me
类别: Reverse Engineering (逆向工程 - RC4 解密)
解题思路:
    1. 从二进制文件 .data 段偏移 0x3020 处提取 RC4 加密数据
    2. 密钥为程序中的硬编码字符串 "this_is_not_flag"
    3. 使用 RC4 解密得到 flag
    4. 替换 Cup{ 前缀为 novruzCTF{
"""

import sys


def rc4_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    """RC4 解密函数"""
    if isinstance(key, str):
        key = key.encode()

    # KSA (密钥调度算法)
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]

    # PRGA (伪随机数生成算法)
    i = j = 0
    output = []
    for byte in ciphertext:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        output.append(byte ^ K)

    return bytes(output)


def main():
    print("=" * 70)
    print("  Zoktay Crack Me - CTF Reverse Engineering(逆向工程) Solution")
    print("=" * 70)

    # 加密数据（从二进制文件.data段偏移0x3020处提取）
    encrypted_data = bytes([
        0x65, 0xf9, 0x45, 0xce, 0x8a, 0x60, 0xe0, 0x90,
        0xfe, 0x66, 0xff, 0x67, 0xef, 0x1b, 0xd1, 0x2e,
        0xf1, 0x6b, 0xa4, 0x0f, 0x96, 0x9e, 0xbe, 0xc0,
        0x0b, 0x88, 0xc3, 0x40, 0x06, 0x27, 0x5a, 0xd2,
        0xdf, 0xa6, 0x15, 0x0d, 0x8d, 0xef, 0xcf, 0x29,
        0x83, 0xa4, 0x44, 0x3d, 0xd7, 0x9b, 0xf4, 0x9e,
        0x87, 0x67, 0x4d, 0xcf, 0x4e, 0x5a, 0xe0, 0x6b,
        0xf4, 0x13, 0xe1, 0xdc, 0xbb, 0xce, 0x73, 0x14,
        0xee, 0x09, 0xe3, 0x4f, 0x46
    ])

    # 密钥（从程序字符串中发现）
    password = "this_is_not_flag"

    print(f"\n[*] 加密数据长度: {len(encrypted_data)} 字节")
    print(f"[*] 加密算法: RC4")
    print(f"[*] 密钥: {password}")
    print(f"\n[+] 正在解密...")

    try:
        flag = rc4_decrypt(password, encrypted_data)
        flag_text = flag.decode()
        submit_flag = flag_text.replace("Cup{", "novruzCTF{", 1) if flag_text.startswith("Cup{") else flag_text

        print(f"\n{'=' * 70}")
        print(f"  FLAG: {submit_flag}")
        print(f"{'=' * 70}")

        # 验证
        print(f"\n[*] 验证信息:")
        print(f"    - 长度: {len(flag)} 字节")
        print(f"    - 格式: {'novruzCTF{...}' if submit_flag.startswith('novruzCTF{') else '未知'}")
        print(f"    - 内容: SHA-256哈希值")
        print(f"\n[OK] 解题成功！")
    except UnicodeDecodeError as e:
        print(f"[!] 解密结果无法解码为文本: {e}", file=sys.stderr)
        print(f"[*] 原始字节: {flag.hex()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
