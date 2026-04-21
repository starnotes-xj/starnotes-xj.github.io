from pathlib import Path
import random


OUTPUT_PATH = Path("CTF_Writeups/files/The Accursed Lego Bin/output.txt")


def parse_output(path: Path) -> tuple[int, str]:
    seed = None
    flag_hex = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("seed = "):
            seed = int(line.split("=", 1)[1].strip())
        elif line.startswith("flag = "):
            flag_hex = line.split("=", 1)[1].strip()
    if seed is None or flag_hex is None:
        raise ValueError("invalid output.txt format")
    return seed, flag_hex


def integer_nth_root(value: int, n: int) -> int:
    lo, hi = 0, 1
    while hi**n <= value:
        hi <<= 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid**n <= value:
            lo = mid
        else:
            hi = mid
    return lo


def hex_to_bits(flag_hex: str) -> list[str]:
    data = bytes.fromhex(flag_hex)
    return list("".join(f"{byte:08b}" for byte in data))


def inverse_shuffle(bits: list[str], round_seed: int) -> list[str]:
    perm = list(range(len(bits)))
    random.seed(round_seed)
    random.shuffle(perm)

    original = [None] * len(bits)
    for new_pos, old_pos in enumerate(perm):
        original[old_pos] = bits[new_pos]
    return original


def bits_to_text(bits: list[str]) -> str:
    data = bytes(
        int("".join(bits[offset:offset + 8]), 2)
        for offset in range(0, len(bits), 8)
    )
    return data.decode("ascii")


def solve() -> str:
    enc_seed, flag_hex = parse_output(OUTPUT_PATH)
    shuffle_seed = integer_nth_root(enc_seed, 7)
    if shuffle_seed**7 != enc_seed:
        raise ValueError("7th root recovery failed")

    bits = hex_to_bits(flag_hex)
    for i in range(9, -1, -1):
        bits = inverse_shuffle(bits, shuffle_seed * (i + 1))
    return bits_to_text(bits)


def main() -> None:
    print(solve())


if __name__ == "__main__":
    main()
