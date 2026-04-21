#!/usr/bin/env python3
"""
kashiCTF - Secret of Mahabharata

题目描述：秘密信息每隔64年重新加密（Base64编码），历经3136年
解题思路：3136 ÷ 64 = 49 次 Base64 编码，循环解码即可还原明文
Flag: kashiCTF{th3_s3cr3t_0f_mah4bh4r4t4_fr0m_3136_BCE}
"""

import base64

def main():
    # 读取被多次 Base64 编码的密文文件
    with open("secret_message.txt", "r") as f:
        data = f.read().strip()

    # 循环解码：每次尝试 Base64 解码，失败则说明已到达明文
    i = 0
    while True:
        try:
            decoded = base64.b64decode(data).decode("utf-8")
            data = decoded.strip()
            i += 1
            print(f"第 {i} 次解码完成, 剩余大小: {len(data)} bytes")
        except Exception:
            print(f"共解码 {i} 次")
            print(f"Flag: {data}")
            break

    # 注意：原始 flag 格式为 flag{...}，需手动替换为 kashiCTF{...}

if __name__ == "__main__":
    main()
