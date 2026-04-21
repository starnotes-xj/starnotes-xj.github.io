"""
CPCTF - L0v3 PDF

题目提示 PDF 中除了可见文本还有别的数据。这个脚本直接从 PDF 原始字节流里
提取所有 `CPCTF{...}` 样式的候选，并优先输出非 dummy 的那个结果。
"""

from __future__ import annotations

import re
from pathlib import Path


FLAG_PATTERN = re.compile(rb"CPCTF\{[^}\r\n]+\}")


def find_flag(pdf_path: Path) -> str:
    data = pdf_path.read_bytes()
    candidates = [match.decode() for match in FLAG_PATTERN.findall(data)]
    if not candidates:
        raise ValueError("未在 PDF 原始字节流中找到任何 CPCTF flag 候选")

    for candidate in candidates:
        if "dummy" not in candidate.lower():
            return candidate
    return candidates[0]


def main() -> None:
    pdf_path = Path(__file__).resolve().parents[1] / "files" / "L0v3_PDF" / "il0v3pdfs.pdf"
    print(find_flag(pdf_path))


if __name__ == "__main__":
    main()
