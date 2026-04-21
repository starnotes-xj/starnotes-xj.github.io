import re
from pathlib import Path

BINARY_PATH = Path("CTF_Writeups/files/hidden/hidden")
FLAG_PATTERN = re.compile(rb"CPCTF\{[^}]+\}")


def extract_flag(binary_path: Path) -> str:
    """从二进制内容中提取符合 CPCTF flag 格式的字符串。"""
    binary_data = binary_path.read_bytes()
    flag_match = FLAG_PATTERN.search(binary_data)
    if flag_match is None:
        raise RuntimeError("flag not found in binary")
    return flag_match.group().decode("utf-8")


def main() -> None:
    flag = extract_flag(BINARY_PATH)
    print(flag)


if __name__ == "__main__":
    main()
