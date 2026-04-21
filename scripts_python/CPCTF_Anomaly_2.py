#!/usr/bin/env python3
"""CPCTF - Anomaly 2 解题脚本。

题目脚本的关键错误是把 flag 整数当成了模数：

    c = pow(n, e, m)

其中 m = bytes_to_long(flag)。因此每一组输出都满足：

    n_i ** e_i - c_i = k_i * m

对两组数据求 gcd，就能恢复 m 的倍数。若两个 k_i 还有额外公共因子，
gcd 会等于 small_factor * m；再结合 flag 格式和原同余式验证即可去掉该因子。
"""

from __future__ import annotations

import math
import re
from pathlib import Path

FLAG_PREFIX = "CPCTF{"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "files" / "Anomaly_2" / "output.txt"


def long_to_bytes(value: int) -> bytes:
    """把非负整数转换为最短的大端字节串。"""
    if value == 0:
        return b"\x00"
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def parse_output(path: Path) -> dict[str, int]:
    """从 output.txt 中解析 n1/e1/c1/n2/e2/c2。"""
    text = path.read_text()
    values = {
        name: int(number)
        for name, number in re.findall(r"^(n\d+|e\d+|c\d+)\s*=\s*(\d+)$", text, re.MULTILINE)
    }
    missing = {"n1", "e1", "c1", "n2", "e2", "c2"} - values.keys()
    if missing:
        raise ValueError(f"{path} 缺少字段: {', '.join(sorted(missing))}")
    return values


def recover_flag(values: dict[str, int]) -> str:
    """利用 gcd(n_i ** e_i - c_i) 恢复 flag，并用原同余式验证。"""
    diff1 = pow(values["n1"], values["e1"]) - values["c1"]
    diff2 = pow(values["n2"], values["e2"]) - values["c2"]
    common = math.gcd(diff1, diff2)

    # common 一定是 m 的倍数，但可能因为两个商 k_i 也有公共因子而变成 k*m。
    # 本题里额外因子为 2；这里扫描小 cofactor，并用 flag 格式和原等式双重确认。
    for cofactor in range(1, 10_000):
        if common % cofactor != 0:
            continue

        candidate_m = common // cofactor
        try:
            flag = long_to_bytes(candidate_m).decode()
        except UnicodeDecodeError:
            continue

        if not flag.startswith(FLAG_PREFIX) or not flag.endswith("}"):
            continue
        if pow(values["n1"], values["e1"], candidate_m) != values["c1"]:
            continue
        if pow(values["n2"], values["e2"], candidate_m) != values["c2"]:
            continue
        return flag

    raise ValueError("未能恢复出符合格式且通过同余验证的 flag")


def main() -> None:
    values = parse_output(OUTPUT_PATH)
    print(recover_flag(values))


if __name__ == "__main__":
    main()
