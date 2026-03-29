#!/usr/bin/env python3
"""
题目名称: Echoes of the Serpent
类别: Crypto (CBC-MAC 长度扩展攻击)
解题思路:
    1. 已知 MAC("hello_world") 和 MAC("get_flag") 的值
    2. 利用 CBC-MAC 的长度扩展漏洞构造伪造消息
    3. block2 = MAC(hello_world) XOR pad(get_flag)
    4. 伪造消息 = pad(hello_world) + block2，MAC 不变
"""


def main():
    # 已知的 MAC 值
    known_mac = bytes.fromhex("77ec0fdf191b1011b974864b443a60ad")
    oracle_mac = bytes.fromhex("162cb90b16adeb0dcdc9776c3af7b324")

    # 填充到 16 字节块
    hello_padded = b"hello_world" + b'\x00' * 5    # 16 bytes
    getflag_padded = b"get_flag" + b'\x00' * 8      # 16 bytes

    # 构造伪造块: block2 = MAC(hello_world) XOR pad(get_flag)
    block2 = bytes(a ^ b for a, b in zip(known_mac, getflag_padded))
    forged_msg = hello_padded + block2

    print("Prophecy (hex):", forged_msg.hex())
    print("Seal (hex):", oracle_mac.hex())


if __name__ == "__main__":
    main()
