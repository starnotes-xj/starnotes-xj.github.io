#!/usr/bin/env python3
"""
ACSC Qualification 2026 - SafeShell

利用点：
1. 服务端使用 AES-CBC 加密保存的 JSON state
2. restore 时不校验完整性，直接解密并 json.loads
3. 第一块明文可预测，因此可以通过修改 IV 把
   {"admin": false,
   改成
   {"admin": true,

该脚本只依赖 Python 标准库，可直接打远程服务：
python CTF_Writeups/scripts_python/ACSC2026Qualification_SafeShell.py --host port.dyn.acsc.land --port 31582
"""

from __future__ import annotations

import argparse
import re
import socket
import sys


# 首块明文必须与目标明文等长（本题恰好都是 16 字节）
ORIGINAL_BLOCK = b'{"admin": false,'
TARGET_BLOCK = b'{"admin": true, '
PROMPT = b"> "
BLOCK_SIZE = 16


def recv_until(sock: socket.socket, marker: bytes = PROMPT) -> bytes:
    """持续接收直到看到交互提示符。"""
    buffer = bytearray()
    while marker not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buffer.extend(chunk)
    return bytes(buffer)


def xor3(left: bytes, middle: bytes, right: bytes) -> bytes:
    """逐字节执行 left ^ middle ^ right。"""
    return bytes(a ^ b ^ c for a, b, c in zip(left, middle, right))


def exploit(host: str, port: int) -> bytes:
    """连远程服务，伪造管理员状态并返回最终输出。"""
    if len(ORIGINAL_BLOCK) != BLOCK_SIZE or len(TARGET_BLOCK) != BLOCK_SIZE:
        raise ValueError("首块明文长度异常，无法执行 CBC 首块篡改")

    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(10)

        banner = recv_until(sock)

        # 1) 获取服务端返回的 state 密文
        sock.sendall(b"save\n")
        save_output = recv_until(sock)
        match = re.search(rb"Saved shell state: ([0-9a-f]+)", save_output)
        if not match:
            raise RuntimeError("未能从 save 输出中提取密文")

        ciphertext = bytes.fromhex(match.group(1).decode())
        if len(ciphertext) < BLOCK_SIZE * 2:
            raise RuntimeError("密文长度不足，无法分离 IV 与首个密文块")
        original_iv = ciphertext[:16]
        encrypted_body = ciphertext[16:]

        # 2) 利用 CBC 首块公式 P0 = D(C0) ^ IV，构造新的 IV
        forged_iv = xor3(original_iv, ORIGINAL_BLOCK, TARGET_BLOCK)
        forged_ciphertext = (forged_iv + encrypted_body).hex().encode()

        # 3) 恢复伪造后的状态
        sock.sendall(b"restore " + forged_ciphertext + b"\n")
        restore_output = recv_until(sock)
        if b"Restored saved shell state" not in restore_output:
            raise RuntimeError("restore 未成功，无法继续获取 flag")

        # 4) 管理员状态已被翻转为 True，直接读取 flag
        sock.sendall(b"flag\n")
        flag_output = recv_until(sock)

        return banner + save_output + restore_output + flag_output


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Exploit ACSC Qualification 2026 SafeShell")
    parser.add_argument("--host", default="port.dyn.acsc.land", help="目标主机")
    parser.add_argument("--port", type=int, default=31582, help="目标端口")
    args = parser.parse_args()

    try:
        output = exploit(args.host, args.port)
    except OSError as err:
        raise SystemExit(f"连接目标失败: {args.host}:{args.port} ({err})") from err

    print(output.decode("utf-8", "replace"), end="")


if __name__ == "__main__":
    main()
