#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
putcCTF - 文件里面有什么（beautiful）自动化复现脚本

功能概览：
1) 从 PNG 中定位 IEND，提取尾随 payload。
2) 从尾随 payload 中裁剪出有效 ZIP（去除 EOCD 后垃圾数据）和附带 JPEG。
3) 从 PNG 的 XMP 元数据提取 sigma2（Base64 解码后为 " Ishmael."）。
4) 从 PNG 的 RGB-LSB 提取 UTF-16BE 文本前缀（"You can call me"）。
5) 拼接得到 ZIP 密码："You can call me Ishmael."。
6) 解密 ZIP 得到 n01z.wav。
7) 生成频谱图用于读取隐藏文本（可见 CHAOS_BLURRING）。

依赖：
- pyzipper
- pillow
- numpy
- matplotlib
"""

from __future__ import annotations

import base64
import re
import struct
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyzipper
from PIL import Image


def parse_png_iend_end(data: bytes) -> int:
    """解析 PNG chunk，返回 IEND 结束偏移（即尾随 payload 起点）。"""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("input is not PNG")

    offset = 8
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        ctype = data[offset + 4 : offset + 8]
        data_end = offset + 8 + length
        crc_end = data_end + 4
        if crc_end > len(data):
            raise ValueError("truncated PNG before CRC")

        offset = crc_end
        if ctype == b"IEND":
            return offset

    raise ValueError("IEND not found")


def carve_zip_from_tail(tail: bytes) -> tuple[bytes, bytes]:
    """从 tail 中裁剪有效 ZIP 与其后附加数据（这里是 JPEG）。"""
    eocd = tail.find(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("EOCD not found in tail")

    comment_len = struct.unpack("<H", tail[eocd + 20 : eocd + 22])[0]
    zip_end = eocd + 22 + comment_len
    return tail[:zip_end], tail[zip_end:]


def extract_sigma2_from_xmp(data: bytes) -> str:
    """从 XMP 中提取 <b64:c2lnbWEy>...</b64:c2lnbWEy> 对应值并 Base64 解码。"""
    # c2lnbWEy == base64("sigma2")
    m = re.search(rb"<b64:c2lnbWEy>([^<]+)</b64:c2lnbWEy>", data)
    if not m:
        raise ValueError("sigma2 not found in XMP")

    b64_val = m.group(1).decode("ascii")
    decoded = base64.b64decode(b64_val + "=" * ((4 - len(b64_val) % 4) % 4))
    return decoded.decode("utf-8", errors="replace")


def extract_rgb_lsb_prefix_text(png_path: Path) -> str:
    """
    提取 RGB 三通道最低位，按位拼接成字节流：
    - 前 4 字节是长度字段（此题给了 240，但后面存在大量噪声）
    - 实际可读提示在最前面，以 UTF-16BE + NUL 结束
    """
    img = Image.open(png_path).convert("RGBA")
    pixels = list(img.getdata())

    bits = []
    for r, g, b, _a in pixels:
        bits.extend([r & 1, g & 1, b & 1])

    out = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        out[i >> 3] |= (bit & 1) << (7 - (i & 7))

    data = bytes(out)
    _declared_len = int.from_bytes(data[:4], "big")

    # 读取前 256 个 UTF-16BE 字符，截到第一个 NUL
    raw = data[4 : 4 + 256 * 2]
    text = raw.decode("utf-16-be", errors="replace")
    text = text.split("\x00", 1)[0]
    return text


def extract_wav_from_zip(zip_path: Path, password: str, wav_name: str, out_wav: Path) -> None:
    """用 AES ZIP 密码解密提取 WAV。"""
    with pyzipper.AESZipFile(zip_path) as zf:
        zf.setpassword(password.encode("utf-8"))
        data = zf.read(wav_name)
    out_wav.write_bytes(data)


def save_spectrogram(wav_path: Path, out_png: Path) -> None:
    """生成频谱图，手工读取隐藏文本。"""
    import wave

    with wave.open(str(wav_path), "rb") as wf:
        channels = wf.getnchannels()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    audio = np.frombuffer(raw, dtype=np.int16)
    if channels > 1:
        audio = audio.reshape(-1, channels)[:, 0]

    plt.figure(figsize=(14, 5))
    plt.specgram(audio.astype(np.float32), NFFT=512, Fs=framerate, noverlap=384, cmap="gray")
    plt.ylim(0, 3000)
    plt.xlabel("Time (s)")
    plt.ylabel("Hz")
    plt.colorbar(label="dB")
    plt.tight_layout()
    plt.savefig(out_png, dpi=220)
    plt.close()


def main() -> None:
    root = Path("D:/GolandProjects/BIGC_CTF_Writeups")
    png_path = root / "beautiful"

    # 输出目录（与项目附件目录保持一致）
    out_dir = root / "CTF_Writeups" / "files" / "beautiful"
    out_dir.mkdir(parents=True, exist_ok=True)

    png_data = png_path.read_bytes()

    # 1) 从 PNG 中提取尾随 payload
    iend_end = parse_png_iend_end(png_data)
    tail = png_data[iend_end:]

    # 2) 裁剪 ZIP + JPEG
    zip_bytes, jpg_bytes = carve_zip_from_tail(tail)
    zip_path = out_dir / "beautiful_clean.zip"
    jpg_path = out_dir / "beautiful_extra.jpg"
    zip_path.write_bytes(zip_bytes)
    jpg_path.write_bytes(jpg_bytes)

    # 3) XMP 的 sigma2 片段
    sigma2 = extract_sigma2_from_xmp(png_data)  # " Ishmael."

    # 4) RGB-LSB 文本前缀
    prefix = extract_rgb_lsb_prefix_text(png_path)  # "You can call me"

    # 5) 拼接密码并解压 WAV
    password = prefix + sigma2
    wav_name = "n01z.wav"
    wav_path = out_dir / wav_name
    extract_wav_from_zip(zip_path, password, wav_name, wav_path)

    # 6) 生成频谱图
    spec_path = out_dir / "n01z_spectrogram.png"
    save_spectrogram(wav_path, spec_path)

    print("[+] ZIP password:", repr(password))
    print("[+] carved zip:", zip_path)
    print("[+] carved jpg:", jpg_path)
    print("[+] extracted wav:", wav_path)
    print("[+] spectrogram:", spec_path)
    print("[+] spectrogram text (manual read): CHAOS_BLURRING")


if __name__ == "__main__":
    main()
