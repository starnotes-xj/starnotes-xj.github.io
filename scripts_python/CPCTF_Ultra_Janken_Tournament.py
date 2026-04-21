"""
CPCTF - Ultra Janken Tournament

题目会先生成 100 个隐藏参赛者的 120 长度“猜拳战力表”，每一列都来自同一个
nextrand() 线性变换的幂序列。我们可以提交自己的 120 个 64-bit 整数作为第 101 位
参赛者，然后在每一轮看到随机 luck pattern 之后翻转若干 bit，要求最终 winner
恰好等于当轮给出的 player_no。

解法摘要：
1. 把 nextrand 视为 GF(2) 上的 64 维线性变换 T。
2. 求出 T 的一个 64 次消去多项式 m(x)，于是只要 luck pattern 的系数向量属于
   <m(x)> 生成的线性码，100 个隐藏参赛者的总贡献就会整体归零。
3. 再把自己提交的 strategy 设计成一个“读出前 8 个 message bit”的线性映射，
   这样有效 codeword 会把 winner 直接编码成一个 0..255 的值；只要这个值 mod 101
   等于题目要求的 player_no，就能稳定获胜。
4. 在线部分只剩一个最近码字搜索问题。这里用按高位 message bit 展开的 beam search，
   并用“已经被冻结、不会再被未来变量影响的输出位”作为剪枝评分。
"""

from __future__ import annotations

import argparse
import re
import socket
from dataclasses import dataclass


HOST = "133.88.122.244"
PORT = 32035
STRATEGY_LEN = 120

# 对应精确版 nextrand():
# n ^= n << 13
# n ^= n >> 7
# n ^= n << 17
# n &= (1 << 64) - 1
#
# 计算得到的一个消去多项式：
# x^64 + x^51 + x^49 + x^48 + x^46 + x^45 + x^43 + x^42 + x^41 + x^39
# + x^38 + x^35 + x^34 + x^33 + x^32 + x^31 + x^30 + x^23 + x^21 + x^20
# + x^17 + x^16 + x^14 + x^13 + x^10 + x^8 + x^4 + x^3 + x^2 + 1
TAPS = [
    0,
    2,
    3,
    4,
    8,
    10,
    13,
    14,
    16,
    17,
    20,
    21,
    23,
    30,
    31,
    32,
    33,
    34,
    35,
    38,
    39,
    41,
    42,
    43,
    45,
    46,
    48,
    49,
    51,
    64,
]

PROMPT = "What will you do? [C]heat the luck / [G]o Janken!: "
TARGET_PATTERN = re.compile(r"Your Number is No: (\d+)")
LUCK_PATTERN = re.compile(r"Current Luck Pattern: ([01]{120})")
FLAG_PATTERN = re.compile(r"(CPCTF\{[^\r\n]+\}|FLAG\{[^\r\n]+\})")


@dataclass(frozen=True)
class SolverContext:
    """保存 beam search 所需的全部预计算结果。"""

    player_strategy: list[int]
    var_masks: list[int]
    frozen_masks: list[int]
    const_cache: dict[int, int]


def build_player_strategy() -> list[int]:
    """
    让自己的贡献恰好恢复 codeword 对应 message 的低 8 bit。

    由于 taps 里包含 2/3/4，前 8 个 codeword bit 不是直接等于 message bit，
    需要先把 g_0..g_7 用 c_0..c_7 的线性组合写出来，再反推出每个 c_j 应携带哪些
    目标位。
    """

    # message bit g_i 对应的 codeword 低 8 位线性表达式。
    message_masks: list[int] = []
    for i in range(8):
        mask = 1 << i
        for tap in TAPS[1:]:
            if tap <= i:
                mask ^= message_masks[i - tap]
        message_masks.append(mask)

    strategy = [0] * STRATEGY_LEN
    for codeword_bit in range(8):
        value = 0
        for message_bit, mask in enumerate(message_masks):
            if (mask >> codeword_bit) & 1:
                value |= 1 << message_bit
        strategy[codeword_bit] = value
    return strategy


def build_solver_context() -> SolverContext:
    """预计算 beam search 用到的变量掩码、冻结位掩码和常量部分。"""

    player_strategy = build_player_strategy()

    # 固定 message 的低 8 位；剩余 48 位由 beam search 在线决定。
    free_positions = list(range(8, 56))
    free_positions.sort(reverse=True)

    var_masks: list[int] = []
    for position in free_positions:
        mask = 0
        for tap in TAPS:
            bit_index = position + tap
            if bit_index < STRATEGY_LEN:
                mask |= 1 << bit_index
        var_masks.append(mask)

    future_union = [0] * (len(var_masks) + 1)
    running = 0
    for idx in range(len(var_masks) - 1, -1, -1):
        running |= var_masks[idx]
        future_union[idx] = running

    all_bits = (1 << STRATEGY_LEN) - 1
    frozen_masks = [all_bits ^ future_union[idx] for idx in range(len(var_masks) + 1)]

    const_cache: dict[int, int] = {}
    for value in range(256):
        mask = 0
        for bit in range(8):
            if (value >> bit) & 1:
                for tap in TAPS:
                    bit_index = bit + tap
                    if bit_index < STRATEGY_LEN:
                        mask ^= 1 << bit_index
        const_cache[value] = mask

    return SolverContext(
        player_strategy=player_strategy,
        var_masks=var_masks,
        frozen_masks=frozen_masks,
        const_cache=const_cache,
    )


def solve_pattern(bits: str, target: int, ctx: SolverContext, width: int) -> tuple[int, list[int]]:
    """
    找到一个离当前 luck pattern 最近的合法 codeword，使得自己的贡献 mod 101 == target。

    返回值：
    - chosen_value: 该 codeword 编码出的 0..255 数值
    - flips: 需要翻转的索引列表
    """

    received_mask = int(bits[::-1], 2)
    best_distance = 10**9
    best_mask = 0
    best_value = 0

    # 0..255 中与 target 同余的候选只有这三个。
    for value in (target, target + 101, target + 202):
        if value >= 256:
            continue

        current_states = {
            ctx.const_cache[value]: ((ctx.const_cache[value] ^ received_mask) & ctx.frozen_masks[0]).bit_count()
        }

        for depth, variable_mask in enumerate(ctx.var_masks, start=1):
            frozen_mask = ctx.frozen_masks[depth]
            next_states: dict[int, int] = {}

            for partial_mask in current_states:
                score_without_variable = ((partial_mask ^ received_mask) & frozen_mask).bit_count()
                previous = next_states.get(partial_mask)
                if previous is None or score_without_variable < previous:
                    next_states[partial_mask] = score_without_variable

                partial_with_variable = partial_mask ^ variable_mask
                score_with_variable = ((partial_with_variable ^ received_mask) & frozen_mask).bit_count()
                previous = next_states.get(partial_with_variable)
                if previous is None or score_with_variable < previous:
                    next_states[partial_with_variable] = score_with_variable

            if len(next_states) > width:
                best_items = sorted(next_states.items(), key=lambda item: item[1])[:width]
                current_states = dict(best_items)
            else:
                current_states = next_states

        for candidate_mask in current_states:
            distance = (candidate_mask ^ received_mask).bit_count()
            if distance < best_distance:
                best_distance = distance
                best_mask = candidate_mask
                best_value = value

    corrected_bits = "".join("1" if (best_mask >> idx) & 1 else "0" for idx in range(STRATEGY_LEN))
    flips = [idx for idx, (left, right) in enumerate(zip(bits, corrected_bits)) if left != right]
    return best_value, flips


class Remote:
    """极简 socket 封装，按 prompt 同步远端输出。"""

    def __init__(self, host: str, port: int) -> None:
        self.sock = socket.create_connection((host, port), timeout=30)
        self.sock.settimeout(120)
        self.buffer = b""

    def recv_until(self, marker: str) -> str:
        encoded = marker.encode()
        while encoded not in self.buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError(self.buffer.decode("utf-8", errors="replace"))
            self.buffer += chunk

        idx = self.buffer.index(encoded) + len(encoded)
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

    def send(self, data: str) -> None:
        self.sock.sendall(data.encode())

    def close(self) -> None:
        self.sock.close()


def solve_remote(host: str, port: int, width: int, verbose: bool) -> str:
    """完整跑通远端 20 轮并提取最终 flag。"""

    ctx = build_solver_context()
    remote = Remote(host, port)

    try:
        remote.recv_until("Your Strategy: ")
        remote.send(" ".join(map(str, ctx.player_strategy)) + "\n")

        block = remote.recv_until(PROMPT)
        total_flips = 0

        for round_idx in range(20):
            target_match = TARGET_PATTERN.search(block)
            luck_match = LUCK_PATTERN.search(block)
            if target_match is None or luck_match is None:
                raise ValueError("无法从服务输出中解析当前轮次的 player_no / luck pattern")

            target = int(target_match.group(1))
            luck_bits = luck_match.group(1)
            chosen_value, flips = solve_pattern(luck_bits, target, ctx, width)
            total_flips += len(flips)

            if verbose:
                print(
                    f"round {round_idx + 1}: target={target} "
                    f"chosen={chosen_value} flips={len(flips)} total={total_flips}"
                )

            # 一次性把整轮输入推给服务端，避免 400+ 次网络往返。
            remote.send("".join(f"C\n{idx}\n" for idx in flips) + "G\n")

            # 每次 cheat 后，服务端都会重新打印同一个 action prompt；把这些 prompt 全部吃掉。
            for _ in range(len(flips)):
                remote.recv_until(PROMPT)

            if round_idx != 19:
                block = remote.recv_until(PROMPT)

        trailer = remote.recv_all()
    finally:
        remote.close()

    flag_match = FLAG_PATTERN.search(trailer)
    if flag_match is None:
        raise ValueError("20 轮结束后未在服务输出中找到 flag")
    return flag_match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve CPCTF Ultra Janken Tournament")
    parser.add_argument("--host", default=HOST, help="challenge host")
    parser.add_argument("--port", type=int, default=PORT, help="challenge port")
    parser.add_argument("--width", type=int, default=1000, help="beam width")
    parser.add_argument("--quiet", action="store_true", help="hide per-round logs")
    args = parser.parse_args()

    flag = solve_remote(args.host, args.port, args.width, not args.quiet)
    print(flag)


if __name__ == "__main__":
    main()
