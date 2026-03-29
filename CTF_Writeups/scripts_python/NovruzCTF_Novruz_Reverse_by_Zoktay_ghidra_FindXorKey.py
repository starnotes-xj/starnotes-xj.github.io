#!/usr/bin/env python3
"""
题目名称: Novruz Reverse by Zoktay (Ghidra 脚本)
类别: Reverse Engineering (逆向工程)
说明: 此脚本为 Ghidra 内部运行的 Jython 脚本，
      用于自动从 xor_decrypt 函数中提取 XOR key。
      不能直接用 python3 运行，需通过 Ghidra Headless 或 GUI 加载。
用法: 在 Ghidra 中通过 Script Manager 运行，
      或通过 analyzeHeadless -postScript 调用。
"""

# 以下代码在 Ghidra Jython 环境中执行
# @category CTF

import re
from ghidra.program.model.symbol import SymbolType  # noqa: F401 (Ghidra 内置)

# 目标函数的 mangled name
TARGET_SYMBOL = "_Z11xor_decryptPcPKcmc"

# 查找函数：先按符号名精确匹配
st = currentProgram.getSymbolTable()  # noqa: F821
func = None

for sym in st.getSymbols(TARGET_SYMBOL):
    if sym.getSymbolType() == SymbolType.FUNCTION:
        func = getFunctionAt(sym.getAddress())  # noqa: F821
        break

# 如果精确匹配失败，按名称模糊搜索
if func is None:
    fm = currentProgram.getFunctionManager()  # noqa: F821
    it = fm.getFunctions(True)
    for f in it:
        if "xor_decrypt" in f.getName():
            func = f
            break

if func is None:
    print("FOUND_KEY=")
    exit(0)

# 遍历函数指令，查找 XOR al, 0xNN 模式
listing = currentProgram.getListing()  # noqa: F821
ins_iter = listing.getInstructions(func.getBody(), True)
key = ""
for ins in ins_iter:
    s = ins.toString()
    m = re.search(r"xor\s+al,\s*0x([0-9a-fA-F]{1,2})", s, re.IGNORECASE)
    if m:
        key = m.group(1)
        break

print("FOUND_KEY=0x%s" % key)
