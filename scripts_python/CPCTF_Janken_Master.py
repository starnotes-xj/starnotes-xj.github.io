"""
CPCTF - Janken Master

这题的核心漏洞不是“预测 xoroshiro128+ 的普通输出”，而是服务端直接把用户输入
拆成 128 bit 状态，却没有禁止 xoroshiro128+ 的非法全零状态。

利用步骤：
1. 输入十进制幸运数字 24197857200151252728969465429440056815。
2. 服务器会先执行一次与常量 `0x1234567890abcdef1234567890abcdef` 的异或，
   结果正好得到内部种子 0。
3. xoroshiro128+ 在 `(s0, s1) = (0, 0)` 时会永久输出 0，因此 99 个 NPC 的手势全是 Rock。
4. 我们选择 Paper（2），即可成为唯一赢家并拿到 flag。

脚本支持两种用途：
- 默认本地验证全零状态确实会让 `next() % 3` 永远为 0。
- 加上 `--remote` 时自动连接题目服务并拿到 flag。
"""

from __future__ import annotations

import argparse
import re
import socket


HOST = "133.88.122.244"
PORT = 32212
NPC_COUNT = 99
SEED_MASK = 0x1234567890ABCDEF1234567890ABCDEF
EXPLOIT_SEED = SEED_MASK
WINNING_HAND = 2  # 2 = Paper，对应击败全体 Rock NPC。
FLAG_PATTERN = re.compile(r"(CPCTF\{[^\r\n]+\}|FLAG\{[^\r\n]+\})")


class Xoroshiro128Plus:
    """按题目附件原样实现 xoroshiro128+，用于本地验证 exploit 条件。"""

    MASK = 0xFFFFFFFFFFFFFFFF

    def __init__(self, seed: int) -> None:
        self.s = [seed >> 64 & self.MASK, seed & self.MASK]

    @staticmethod
    def rotl(x: int, k: int) -> int:
        return ((x << k) | (x >> (64 - k))) & Xoroshiro128Plus.MASK

    def next(self) -> int:
        s0 = self.s[0]
        s1 = self.s[1]

        result = (self.rotl((s0 + s1) & self.MASK, 17) + s0) & self.MASK
        s1 ^= s0
        self.s[0] = (self.rotl(s0, 49) ^ s1 ^ ((s1 << 21) & self.MASK)) & self.MASK
        self.s[1] = self.rotl(s1, 28)
        return result


class Remote:
    """极简 socket 封装，按提示符同步读取远端输出。"""

    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.create_connection((host, port), timeout=30)
        self.sock.settimeout(30)
        self.buffer = b""

    def recv_until(self, marker: str) -> str:
        target = marker.encode()
        while target not in self.buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError(self.buffer.decode("utf-8", errors="replace"))
            self.buffer += chunk

        idx = self.buffer.index(target) + len(target)
        out = self.buffer[:idx]
        self.buffer = self.buffer[idx:]
        return out.decode("utf-8", errors="replace")

    def recv_all(self) -> str:
        out = self.buffer
        self.buffer = b""
        while True:
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            out += chunk
        return out.decode("utf-8", errors="replace")

    def send_line(self, line: str) -> None:
        self.sock.sendall((line + "\n").encode())

    def close(self) -> None:
        self.sock.close()


def validate_zero_state() -> None:
    """本地验证：通过 exploit 种子进入全零状态后，99 个 NPC 的手势都为 Rock。"""
    internal_seed = EXPLOIT_SEED ^ SEED_MASK
    rng = Xoroshiro128Plus(internal_seed)
    npc_hands = [rng.next() % 3 for _ in range(NPC_COUNT)]

    if any(hand != 0 for hand in npc_hands):
        raise RuntimeError("unexpected non-rock NPC hand")

    print(f"exploit seed (decimal) = {EXPLOIT_SEED}")
    print(f"internal state = ({internal_seed >> 64}, {internal_seed & Xoroshiro128Plus.MASK})")
    print(f"npc hands = all {NPC_COUNT} times Rock")
    print(f"play hand = {WINNING_HAND} (Paper)")


def solve_remote(host: str, port: int) -> str:
    """连接远端服务，发送 exploit seed 与手势并提取 flag。"""
    remote = Remote(host, port)
    try:
        banner = remote.recv_until("Enter your lucky number (seed): ")
        print(banner, end="")
        remote.send_line(str(EXPLOIT_SEED))

        prompt = remote.recv_until("Your hand (0-2): ")
        print(prompt, end="")
        remote.send_line(str(WINNING_HAND))

        result = remote.recv_all()
        print(result, end="")

        match = FLAG_PATTERN.search(result)
        if match is None:
            raise RuntimeError("flag not found in remote output")
        return match.group(1)
    finally:
        remote.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve CPCTF Janken Master")
    parser.add_argument("--host", default=HOST, help="题目主机")
    parser.add_argument("--port", type=int, default=PORT, help="题目端口")
    parser.add_argument("--remote", action="store_true", help="连接远端服务直接拿 flag")
    args = parser.parse_args()

    validate_zero_state()
    if args.remote:
        flag = solve_remote(args.host, args.port)
        print(f"\nflag = {flag}")


if __name__ == "__main__":
    main()
