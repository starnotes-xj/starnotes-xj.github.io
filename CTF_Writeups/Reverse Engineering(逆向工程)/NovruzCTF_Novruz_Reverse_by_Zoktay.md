# NovruzCTF_rev_zoktay Writeup

## 题目信息
- 比赛：NovruzCTF
- 题目：novruz_rev_zoktay（Reverse）
- 附件：`2a104a33-ad45-4bbf-8937-fb1f9ea85805.bin`（重命名为 `novruz_rev_zoktay`）
- 目标：运行或逆向二进制获取 flag
  - 状态：已解

## Flag
`NovruzCTF{21_Masalli_xeberdar2025}`

## 解题过程

### 1) 基础检查
```bash
file novruz_rev_zoktay
```
结果显示为 ELF 64-bit PIE，可动态链接，未 strip。

### 2) 使用成熟工具定位字符串与函数
**Radare2（命令行）**：
```bash
r2 -q -c "izz~Novruz" novruz_rev_zoktay
r2 -q -c "aaa; afl~xor_decrypt; afl~main" novruz_rev_zoktay
```
可快速看到与 Novruz 相关的字符串片段，以及 `main` 和 `xor_decrypt`（符号未剥离）。

**Ghidra（GUI）**：
- 导入二进制并自动分析
- 在 Symbol Tree 中定位 `xor_decrypt` 与 `main`
- 进入 Decompiler，确认 `xor_decrypt` 为单字节 XOR 解密

### 3) 解码问题与答案
在 Ghidra 的 `main` 中可观察到：
- 多段“加密字符串”写入栈内存
- 统一调用 `xor_decrypt(dst, src, len, key)` 解密
- 解密 key 为 `0x42`

还原得到的问答如下：

| 问题 | 正确答案 |
|---|---|
| Do you want the flag? (yes/no) | `yes` |
| What is the date of Novruz? (number) | `21` |
| Which city hosts the largest Novruz celebrations? (capitalized) | `Masalli` |
| Who is the herald of Novruz? (lowercase) | `xeberdar` |
| Do you love Novruz? (y/n) | `y` |

这些答案与 `strcmp` 对比通过后，程序进入拼接 flag 的分支。

### 4) Flag 生成逻辑
`main` 里直接拼接字符串：
- 初始：`NovruzCTF{`
- 追加：`21_`
- 追加：`Masalli_`
- 追加：`xeberdar`
- 追加：`2025}`

得到完整 flag：
`NovruzCTF{21_Masalli_xeberdar2025}`。

## 漏洞/知识点分析
- **知识点**：简单 XOR 混淆、栈上拼接字符串、`strcmp` 校验流程。
- **保护**：PIE + Canary + NX + Full RELRO，对本题不构成利用点，属于纯逆向恢复逻辑。
- **关键技巧**：不运行二进制也能通过静态分析复原问答与 flag。

## 知识点
- **XOR 混淆** — 单字节 XOR 解密常见于入门逆向
- **栈上拼接** — 多段字符串在栈上拼接后比较
- **strcmp 校验流程** — 逐步问答校验影响 flag 生成路径

## 使用的工具
- Ghidra（反编译/定位 `xor_decrypt` 与 `main`）
- Radare2（字符串/函数列表/反汇编）
- Angr（可选：符号执行验证输入分支）
- file（确认 ELF 类型）

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruz_Reverse_by_Zoktay.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruz_Reverse_by_Zoktay.py`

**额外版本（调用 Radare2）**
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruz_Reverse_by_Zoktay_r2.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruz_Reverse_by_Zoktay_r2.py`

**额外版本（调用 Ghidra Headless）**
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruz_Reverse_by_Zoktay_ghidra.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruz_Reverse_by_Zoktay_ghidra.py`
- Ghidra 脚本：`CTF_Writeups/scripts_python/NovruzCTF_Novruz_Reverse_by_Zoktay_ghidra_FindXorKey.py`

> 脚本用于校验附件并输出已还原的 flag；逆向过程使用成熟工具完成。

## 推荐工具与优化解题流程
1) **Ghidra**：导入二进制 → 自动分析 → Decompiler 查看 `xor_decrypt` 与 `main`，确认 XOR key 与拼接逻辑。
2) **Radare2**：`aaa` 后用 `izz` 看字符串、`afl` 找函数、`pdf` 查看反汇编，快速定位解密逻辑。
3) **Angr（可选）**：用符号执行验证输入是否到达 flag 生成分支。

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Ghidra** | 反编译主流程 | ~10 分钟 | 伪代码直观 | 需要 GUI |
| **Radare2** | 快速定位 | ~5 分钟 | CLI 快速 | 学习成本高 |
| **Angr** | 自动验证 | ~5-30 分钟 | 自动化求解 | 可能慢 |
| **file** | 文件识别 | <1 分钟 | 快速确认类型 | 仅基础信息 |

### 推荐流程
**推荐流程**：file 确认类型 → Radare2 定位函数 → Ghidra 反编译提取 key → 5-10 分钟完成。

## 命令行提取关键数据（无 GUI）

**1) Radare2 字符串与函数**
```bash
r2 -q -c "izz~Novruz" novruz_rev_zoktay
r2 -q -c "aaa; afl~xor_decrypt; afl~main" novruz_rev_zoktay
```

**2) Radare2 反汇编定位解密**
```bash
r2 -q -c "aaa; pdf @ sym._Z11xor_decryptPcPKcmc" novruz_rev_zoktay
r2 -q -c "aaa; pdf @ main" novruz_rev_zoktay
```

**3) Ghidra（GUI）**
- Import → Analyze
- Symbol Tree 定位 `xor_decrypt` 与 `main`
- Decompiler 查看 XOR key 与字符串拼接

**4) Ghidra Headless（命令行）**
```bash
analyzeHeadless /tmp/gh_proj proj -import novruz_rev_zoktay -scriptPath CTF_Writeups/scripts_python -postScript ghidra_FindXorKey.py
```

以上流程可完整复现本题的静态逆向过程。
