#!/usr/bin/env python3
"""
题目名称: Novruz Reverse by Zoktay (Ghidra 版)
类别: Reverse Engineering (逆向工程 - Ghidra Headless 自动分析)
解题思路:
    1. 使用 Ghidra analyzeHeadless 导入二进制文件
    2. 运行自定义 Ghidra 脚本反汇编 xor_decrypt 函数
    3. 从输出中提取 XOR key (0x42)
    4. 结合字符串标记得到 flag: NovruzCTF{21_Masalli_xeberdar2025}
依赖: Ghidra (需配置 PATH 或 GHIDRA_HOME 环境变量)
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

# 内嵌的 Ghidra 分析脚本
GHIDRA_SCRIPT = r"""
#@category CTF
import re
from ghidra.program.model.symbol import SymbolType

name = "_Z11xor_decryptPcPKcmc"
st = currentProgram.getSymbolTable()
func = None

for sym in st.getSymbols(name):
    if sym.getSymbolType() == SymbolType.FUNCTION:
        func = getFunctionAt(sym.getAddress())
        break

if func is None:
    fm = currentProgram.getFunctionManager()
    it = fm.getFunctions(True)
    for f in it:
        if "xor_decrypt" in f.getName():
            func = f
            break

if func is None:
    print("FOUND_KEY=")
    exit(0)

listing = currentProgram.getListing()
ins_iter = listing.getInstructions(func.getBody(), True)
key = ""
for ins in ins_iter:
    s = ins.toString()
    m = re.search(r"xor\s+al,\s*0x([0-9a-fA-F]{1,2})", s, re.IGNORECASE)
    if m:
        key = m.group(1)
        break

print("FOUND_KEY=0x%s" % key)
"""

# 期望的 XOR key
EXPECTED_KEY = "42"
# 最终 flag
FLAG = "NovruzCTF{21_Masalli_xeberdar2025}"


def find_analyze_headless() -> str:
    """查找 Ghidra analyzeHeadless 可执行文件"""
    # 先从 PATH 中查找
    analyze = shutil.which("analyzeHeadless") or shutil.which("analyzeHeadless.bat")
    if analyze:
        return analyze

    # 从 GHIDRA_HOME 环境变量查找
    gh = os.environ.get("GHIDRA_HOME")
    if gh:
        for name in ("analyzeHeadless", "analyzeHeadless.bat"):
            cand = os.path.join(gh, "support", name)
            if os.path.exists(cand):
                return cand

    return ""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "novruz_rev_zoktay"

    # 检查 Ghidra 是否可用
    analyze = find_analyze_headless()
    if not analyze:
        print("[!] 未找到 Ghidra analyzeHeadless，请配置 PATH 或 GHIDRA_HOME。", file=sys.stderr)
        sys.exit(1)

    # 在临时目录中运行 Ghidra Headless 分析
    try:
        with tempfile.TemporaryDirectory(prefix="ghidra_proj_") as workdir:
            script_dir = os.path.join(workdir, "scripts")
            os.makedirs(script_dir, exist_ok=True)
            script_path = os.path.join(script_dir, "FindXorKey.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(GHIDRA_SCRIPT)

            cmd = [
                analyze,
                workdir, "proj",
                "-import", path,
                "-scriptPath", script_dir,
                "-postScript", "FindXorKey.py",
            ]
            out = subprocess.check_output(cmd, text=True, errors="ignore", timeout=120)
    except subprocess.SubprocessError as e:
        print(f"[!] Ghidra 执行失败: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"[!] 文件操作失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 从输出中提取 XOR key
    m = re.search(r"FOUND_KEY=0x([0-9a-fA-F]+)", out)
    if m and m.group(1).lower() == EXPECTED_KEY:
        print(f"[+] 检测到 XOR key = 0x{EXPECTED_KEY}")
        print(FLAG)
    else:
        print("[!] 未能从 Ghidra 输出中解析到 key，请手动检查：", file=sys.stderr)
        print(out, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
