"""
CPCTF - Very Exciting

思路：服务先打印 flag 在某个 (secret_key, exciting_iv) 下的流密码密文，
随后又提供一个“自选 IV + 自选明文”的加密 oracle，而且仍然沿用同一个 secret_key。
只要把用户提交的 IV 设成打印出来的 exciting_iv，并提交与 flag 密文等长的全 0 明文，
服务返回的密文就会退化成裸露的 keystream；再与 flag 密文异或即可恢复 flag。
"""

from __future__ import annotations

import argparse
import re
import socket
from typing import Iterable

# 兼容附件中的中文提示与远端服务中的英文提示。
INITIAL_PROMPTS = [
    b"Enter your boring 'favorite' (Hex): ",
    "输入你无聊的“最爱”（十六进制）: ".encode(),
]
SECOND_PROMPTS = [
    b"Enter your own 'very_exciting' IV (Hex): ",
    b"Enter your own 'very_exciting' IV (Hex):",
]
IV_PATTERN = re.compile(r"exciting_iv[^:：]*[:：]\s*([0-9a-f]+)")
CIPHERTEXT_PATTERN = re.compile(r"=>\s*([0-9a-f]+)")


def recv_until_any(sock: socket.socket, markers: Iterable[bytes]) -> bytes:
    """持续接收数据，直到缓冲区中出现任意一个目标提示。"""
    data = b""
    markers = tuple(markers)
    while True:
        if any(marker in data for marker in markers):
            return data
        chunk = sock.recv(4096)
        if not chunk:
            return data
        data += chunk


def extract_iv_and_ciphertext(banner: str) -> tuple[str, bytes]:
    """从服务横幅中提取 IV 和 flag 密文。"""
    iv_match = IV_PATTERN.search(banner)
    ciphertext_match = CIPHERTEXT_PATTERN.search(banner)
    if iv_match is None or ciphertext_match is None:
        raise ValueError("无法从服务输出中解析 exciting_iv / exciting_flag")
    return iv_match.group(1), bytes.fromhex(ciphertext_match.group(1))


def xor_bytes(left: bytes, right: bytes) -> bytes:
    """逐字节异或两个等长字节串。"""
    if len(left) != len(right):
        raise ValueError("异或双方长度必须一致")
    return bytes(a ^ b for a, b in zip(left, right))


def recover_flag(host: str, port: int) -> str:
    """连接远端服务并自动恢复 flag。"""
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(10)

        # 第一步：读到首个输入提示，解析 flag 密文与对应 IV。
        banner = recv_until_any(sock, INITIAL_PROMPTS).decode(errors="replace")
        exciting_iv_hex, exciting_flag = extract_iv_and_ciphertext(banner)

        # 第二步：发送与 flag 密文等长的全 0 明文。
        zero_plaintext_hex = "00" * len(exciting_flag)
        sock.sendall((zero_plaintext_hex + "\n").encode())

        # 第三步：读到 IV 提示，并复用服务先前打印出来的同一个 IV。
        recv_until_any(sock, SECOND_PROMPTS)
        sock.sendall((exciting_iv_hex + "\n").encode())

        # 第四步：读取后续输出。返回的“密文”此时其实就是 keystream。
        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            response += chunk

    response_text = response.decode(errors="replace")
    keystream_match = CIPHERTEXT_PATTERN.search(response_text)
    if keystream_match is None:
        raise ValueError("无法从二次响应中解析 keystream")

    keystream = bytes.fromhex(keystream_match.group(1))
    flag_bytes = xor_bytes(exciting_flag, keystream)
    return flag_bytes.decode()


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve CPCTF Very Exciting via IV/keystream reuse")
    parser.add_argument("--host", default="133.88.122.244", help="challenge host")
    parser.add_argument("--port", type=int, default=32007, help="challenge port")
    args = parser.parse_args()

    print(recover_flag(args.host, args.port))


if __name__ == "__main__":
    main()
