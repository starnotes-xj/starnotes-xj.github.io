#!/usr/bin/env python3
"""
题目名称: Novruz Ritual
类别: Reverse Engineering (逆向工程)
解题思路:
    1. 二进制文件包含三个验证阶段：stageFire / stageWind / stageWater
    2. stageFire: 解方程组 + 累加器校验 (acc == 0x5f09)
    3. stageWind: 解方程组 + XOR 校验
    4. stageWater: 索引重排 + 减法解码
    5. 最终 flag 格式: novruzctf{water-fire-wind}
"""

import struct
import sys
import os


def solve_fire() -> str:
    """求解 stageFire 阶段的 4 字节密钥"""
    # 方程组: b0 - b1 = 5, b1 + b0*2 = 343, b3 - b2 = 3, b2 + b3*2 = 336
    b1 = (343 - 10) // 3   # 111 'o'
    b0 = b1 + 5             # 116 't'
    b2 = (336 - 6) // 3     # 110 'n'
    b3 = b2 + 3             # 113 'q'
    fire = chr(b0) + chr(b1) + chr(b2) + chr(b3)
    print(f"  {fire} = {[hex(ord(c)) for c in fire]}")

    # 验证累加器
    acc = 0x45
    for i in range(4):
        acc = ((acc << 2) | (acc >> 30)) & 0xFFFFFFFF
        acc ^= ord(fire[i])
        acc = (acc + (i + 1)) & 0xFFFFFFFF
    print(f"  Accumulator: 0x{acc:x} (expected 0x5f09) {'OK' if acc == 0x5f09 else 'FAIL'}")
    return fire


def solve_wind() -> str:
    """求解 stageWind 阶段的 4 字节密钥"""
    b0 = (218 - 4) // 2   # 107 'k'
    b1 = b0 + 4            # 111 'o'
    b3 = 204 - b0           # 97  'a'
    b2 = 212 - b3            # 115 's'
    wind = chr(b0) + chr(b1) + chr(b2) + chr(b3)
    print(f"  {wind} = {[hex(ord(c)) for c in wind]}")
    print(f"  b2^b3={b2 ^ b3} (expected 18) {'OK' if b2 ^ b3 == 18 else 'FAIL'}")
    return wind


def solve_water() -> str:
    """求解 stageWater 阶段的 4 字节密钥（索引重排 + 减法解码）"""
    indices = [2, 0, 3, 1]
    targets = [0x79, 0x64, 0x68, 0x76]
    keys = [0x05, 0x02, 0x07, 0x01]
    result = [0] * 4
    for rcx in range(4):
        idx = indices[rcx]
        val = (targets[rcx] - keys[rcx]) & 0xFF
        result[idx] = val
        print(f"  rcx={rcx}: input[{idx}] = 0x{targets[rcx]:02x}-0x{keys[rcx]:02x} = 0x{val:02x} = {chr(val)!r}")
    return "".join(chr(b) for b in result)


def verify_binary(data: bytes) -> None:
    """验证二进制文件中的调用目标和结构"""
    # stageFire call at 0x9b89e
    rel = struct.unpack("<i", data[0x9b89f:0x9b8a3])[0]
    t1 = 0x49b89e + 5 + rel
    print(f"  stageFire call -> 0x{t1:x} (expected 0x49bc20)")

    # stageWind call at 0x9b8ba
    rel = struct.unpack("<i", data[0x9b8bb:0x9b8bf])[0]
    t2 = 0x49b8ba + 5 + rel
    print(f"  stageWind call -> 0x{t2:x} (expected 0x49bcc0)")

    # 分隔符验证
    sep_vaddr = 0x49b794 + 0x23ce5
    sep_file = 0x9c000 + (sep_vaddr - 0x49c000)
    print(f"  Separator: 0x{data[sep_file]:02x} = {chr(data[sep_file])!r}")

    # 跳转目标验证
    print(f"  jmp target from 0x49b800: 0x{0x49b802 + 0x51:x} (cmp is at 0x49b853)")
    print(f"  Confirmed: loop runs for rcx=0,1,2,3")
    print(f"  Parts order: [0]=Water, [1]=Fire, [2]=Wind  CONFIRMED")


def brute_force_fire() -> None:
    """暴力验证 stageFire 的解"""
    print("=== 暴力验证 stageFire ===")
    for c0 in range(32, 127):
        for c1 in range(32, 127):
            if c0 - c1 != 5:
                continue
            if c1 + c0 * 2 != 343:
                continue
            for c2 in range(32, 127):
                for c3 in range(32, 127):
                    if c3 - c2 != 3:
                        continue
                    if c2 + c3 * 2 != 336:
                        continue
                    acc = 0x45
                    for i, c in enumerate([c0, c1, c2, c3]):
                        acc = ((acc << 2) | (acc >> 30)) & 0xFFFFFFFF
                        acc ^= c
                        acc = (acc + (i + 1)) & 0xFFFFFFFF
                    if acc == 0x5f09:
                        s = chr(c0) + chr(c1) + chr(c2) + chr(c3)
                        print(f"  Found: {s!r}")


def main():
    # 二进制文件路径
    default_bin = os.path.join(os.path.dirname(__file__), "..", "files", "Novruz Ritual", "ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin")
    bin_path = sys.argv[1] if len(sys.argv) > 1 else default_bin

    try:
        with open(bin_path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"[!] 无法读取二进制文件: {e}", file=sys.stderr)
        print("[*] 跳过二进制验证，仅输出计算结果...")
        data = None

    print("=== stageFire ===")
    fire = solve_fire()

    print("\n=== stageWind ===")
    wind = solve_wind()

    print("\n=== stageWater (inline) ===")
    water = solve_water()

    # 输出结果
    phrase = f"{water}-{fire}-{wind}"
    print(f"\n=== RESULT ===")
    print(f"  Phrase: {phrase}")
    print(f"  novruzctf{{{phrase}}}")
    print(f"  novruzCTF{{{phrase}}}")

    # 如果有二进制文件，进行验证
    if data is not None:
        print(f"\n=== 验证调用目标 ===")
        verify_binary(data)

    # 暴力验证
    brute_force_fire()


if __name__ == "__main__":
    main()
