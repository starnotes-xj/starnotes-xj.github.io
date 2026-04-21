"""
CPCTF - 1、0、7

这道题的突破点不是通用 RSA 分解，而是发现模数 N 在十进制下具有：

    1...1 0...0 7...7

这样的拼接结构。脚本会：
1. 读取归档附件里的 N、e、c；
2. 自动识别 N 的数字块长度；
3. 构造 p = (10^k - 1) / 9 与 q = 10^(t+k) + 7；
4. 恢复私钥并解出 flag。
"""

from __future__ import annotations

from itertools import groupby
from pathlib import Path
import re


PARAM_RE = re.compile(r"^(N|e|c)=(\d+)$", re.MULTILINE)


def attachment_path() -> Path:
    """返回归档附件的绝对路径。"""
    base_dir = Path(__file__).resolve().parents[1]
    return base_dir / "files" / "1、0、7" / "107107_b38e4b4bcd49c22b496049abb867695331cdc0f7542dd59288b3597e1b8e4119.txt"


def parse_parameters(text: str) -> dict[str, int]:
    """从题目附件中提取 N、e、c 三个十进制参数。"""
    values = {name: int(value) for name, value in PARAM_RE.findall(text)}
    missing = {"N", "e", "c"} - values.keys()
    if missing:
        raise ValueError(f"附件中缺少参数: {sorted(missing)}")
    return values


def derive_factors(modulus: int) -> tuple[int, int]:
    """
    根据 N = 1^k 0^t 7^k 的十进制结构直接构造两个因子。

    返回:
        (p, q)
    """
    groups = [(digit, len(list(chunk))) for digit, chunk in groupby(str(modulus))]
    if len(groups) != 3:
        raise ValueError(f"N 的分组数量异常: {groups}")

    (first_digit, first_len), (middle_digit, middle_len), (last_digit, last_len) = groups
    if (first_digit, middle_digit, last_digit) != ("1", "0", "7"):
        raise ValueError(f"N 的数字结构不是 1^k 0^t 7^k: {groups}")
    if first_len != last_len:
        raise ValueError(f"N 首尾块长度不一致: {groups}")

    k = first_len
    shift = middle_len + last_len

    p = (10**k - 1) // 9
    q = 10**shift + 7

    if p * q != modulus:
        raise ValueError("按结构推导出的 p、q 无法还原 N")
    return p, q


def int_to_bytes(value: int) -> bytes:
    """把非负整数按大端序转换回原始字节串。"""
    if value < 0:
        raise ValueError("只支持非负整数")
    if value == 0:
        return b"\x00"
    length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "big")


def main() -> None:
    raw_text = attachment_path().read_text(encoding="utf-8")
    params = parse_parameters(raw_text)

    n = params["N"]
    e = params["e"]
    c = params["c"]

    p, q = derive_factors(n)
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, n)

    print(int_to_bytes(m).decode("utf-8"))


if __name__ == "__main__":
    main()
