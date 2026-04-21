#!/usr/bin/env python3

# LCG 参数：state_{n+1} = (A * state_n + C) mod 2^32
A = 1664525
C = 1013904223
STATE_MOD = 1 << 32

# 题目只泄露高 16 位，因此右移 16 位即得到输出
HIGH_BITS_SHIFT = 16
LOW_BITS_RANGE = 1 << HIGH_BITS_SHIFT

# 已知连续输出（position 0-3）
OUTPUTS = [52338, 24512, 16929, 35379]

# 需要预测的目标位置
TARGET_POSITION = 100


def next_state(state: int) -> int:
    """计算 LCG 的下一状态（取模 2^32）。"""
    return (A * state + C) % STATE_MOD


def advance(state: int, steps: int) -> int:
    """将状态向前推进指定步数。"""
    for _ in range(steps):
        state = next_state(state)
    return state


def matches_observed_outputs(state0: int) -> bool:
    """验证候选 state0 是否与已知输出序列一致。"""
    state = state0
    for expected_output in OUTPUTS[1:]:
        state = next_state(state)
        if (state >> HIGH_BITS_SHIFT) != expected_output:
            return False
    return True


def find_candidate_states(first_output: int) -> list[int]:
    """枚举 state0 的低 16 位，并返回匹配输出序列的候选。"""
    candidates: list[int] = []

    for low_bits in range(LOW_BITS_RANGE):
        # state0 高 16 位来自 output0，低 16 位逐个枚举
        state0 = (first_output << HIGH_BITS_SHIFT) | low_bits
        if matches_observed_outputs(state0):
            candidates.append(state0)

    return candidates


def main() -> None:
    first_output = OUTPUTS[0]
    candidates = find_candidate_states(first_output)

    # 若候选不唯一，直接打印并退出
    if len(candidates) != 1:
        print("candidate states:", [hex(value) for value in candidates])
        return

    # 唯一 state0 找到后，推进到目标 position
    state0 = candidates[0]
    target_state = advance(state0, TARGET_POSITION)

    # 输出 state0 与预测结果（高 16 位）
    print("state0 =", state0, hex(state0))
    print("output_100 =", target_state >> HIGH_BITS_SHIFT)


if __name__ == "__main__":
    main()
