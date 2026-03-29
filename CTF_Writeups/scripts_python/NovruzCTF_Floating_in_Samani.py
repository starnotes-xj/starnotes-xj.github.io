#!/usr/bin/env python3
"""
题目名称: XOR 42
类别: PPC / Math (数学运算)
解题思路:
    1. 服务端要求在只能使用加减乘除的表达式中实现 XOR 运算
    2. 利用 banker's rounding 技巧 (6755399441055744 常数) 提取各个 bit
    3. 重建 a XOR 42 的结果：a + 42 - 2*(a AND 42)
    4. 通过 socket 发送 payload 获取 flag
"""

import socket
import sys

# 目标地址（可通过命令行参数覆盖）
TARGET_HOST = "tcp.canyouhack.org"
TARGET_PORT = 10091

# Banker's rounding 魔术常数
MAGIC = 6755399441055744


def build_payload() -> str:
    """
    构造纯算术表达式实现 a XOR 42。
    利用 banker's rounding 技巧提取各个 bit 位。
    """
    return (
        "a + 42"
        f" - 4 * (a / 2 - 63 / 128 + {MAGIC} - {MAGIC})"
        f" + 8 * (a / 4 - 63 / 128 + {MAGIC} - {MAGIC})"
        f" - 16 * (a / 8 - 63 / 128 + {MAGIC} - {MAGIC})"
        f" + 32 * (a / 16 - 63 / 128 + {MAGIC} - {MAGIC})"
        f" - 64 * (a / 32 - 63 / 128 + {MAGIC} - {MAGIC})"
        f" + 128 * (a / 64 - 63 / 128 + {MAGIC} - {MAGIC})"
    )


def main():
    if len(sys.argv) > 2:
        host, port = sys.argv[1], int(sys.argv[2])
    else:
        host, port = TARGET_HOST, TARGET_PORT

    try:
        with socket.create_connection((host, port), timeout=10) as s:
            # 读取服务端欢迎信息
            s.settimeout(2)
            try:
                s.recv(1024)
            except socket.timeout:
                pass

            # 发送 payload
            payload = build_payload()
            s.sendall((payload + "\n").encode())

            # 接收响应
            s.settimeout(5)
            data = b""
            try:
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass

            if data:
                print(data.decode(errors="ignore"), end="")
            else:
                print("[!] 未收到响应", file=sys.stderr)
    except (socket.error, OSError) as e:
        print(f"[!] 连接失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
