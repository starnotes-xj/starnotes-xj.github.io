#!/usr/bin/env python3
"""CPCTF Out of World 题解复现脚本。

解题思路：
1. 读取归档后的 ELF 附件，不依赖运行目标程序。
2. 从 .data 段对应的文件偏移提取两段关键数据：
   - 0x3050: 环境变量校验数组（24 字节）
   - 0x3020: flag 密文数组（41 字节）
3. 根据校验逻辑 `env[i] ^ 0x23 == check[i]` 还原正确环境变量。
4. 根据解码逻辑 `flag[i] = enc[i] ^ key[i % len(key)] ^ 0x45` 还原最终 flag。
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BINARY_PATH = BASE_DIR / "files" / "Out_of_World" / "chal-f7199d01c49d56bebaae2d98ff2b597c"
CHECK_OFFSET = 0x3050
CHECK_LENGTH = 0x18
FLAG_OFFSET = 0x3020
FLAG_LENGTH = 0x29
CHECK_XOR = 0x23
FLAG_XOR = 0x45


def read_slice(path: Path, offset: int, length: int) -> bytes:
    """从题目附件中读取固定偏移的数据。"""
    with path.open("rb") as binary_file:
        binary_file.seek(offset)
        data = binary_file.read(length)
    if len(data) != length:
        raise RuntimeError(f"read {len(data)} bytes at {offset:#x}, expected {length}")
    return data


def recover_secret_key(binary_path: Path) -> str:
    """根据校验数组反推出 getenv 需要的环境变量值。"""
    check_data = read_slice(binary_path, CHECK_OFFSET, CHECK_LENGTH)
    key_bytes = bytes(value ^ CHECK_XOR for value in check_data)
    return key_bytes.decode("ascii")


def recover_flag(binary_path: Path, secret_key: str) -> str:
    """使用恢复出的 key 对密文做循环异或解码。"""
    encrypted_flag = read_slice(binary_path, FLAG_OFFSET, FLAG_LENGTH)
    key_bytes = secret_key.encode("ascii")
    flag_bytes = bytearray()

    for index, encrypted_byte in enumerate(encrypted_flag):
        key_byte = key_bytes[index % len(key_bytes)]
        flag_bytes.append(encrypted_byte ^ key_byte ^ FLAG_XOR)

    return flag_bytes.decode("ascii")


def main() -> None:
    secret_key = recover_secret_key(BINARY_PATH)
    flag = recover_flag(BINARY_PATH, secret_key)

    print(f"secret_key={secret_key}")
    print(flag)


if __name__ == "__main__":
    main()
