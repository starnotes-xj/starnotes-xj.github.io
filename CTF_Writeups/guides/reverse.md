---
title: Reverse 新手上手操作指南
---

# Reverse 新手上手操作指南

Reverse 题最常见的卡点不是“不会读汇编”，而是拿到附件后不知道第一步看什么。入门阶段先建立固定流程：识别文件、找字符串、确认输入来源、找校验逻辑，再决定是否需要 Ghidra、动态调试或脚本复现。

## 这类题先看什么

先问四个问题：

1. 这是什么文件？ELF、PE、Mach-O、脚本还是伪装文件？
2. 程序的输入从哪里来？stdin、argv、环境变量、文件还是网络？
3. 程序在比较什么？`strcmp`、`memcmp`、长度、循环逐字节、异或后比较？
4. flag 是明文、运行时拼接，还是需要解密生成？

如果题目提示了 `getenv`、`argv`、`strcmp`、`xor` 之类关键词，要立刻把它当成主线索。

## 最小工具集

| 工具 | 用途 |
|------|------|
| `file` | 判断文件类型、架构、是否 stripped |
| `strings` | 提取可打印字符串，寻找提示、flag 前缀、环境变量名 |
| Ghidra | 反编译主逻辑、找交叉引用、看伪代码 |
| Python | 离线复现校验逻辑或解密逻辑 |
| gdb / pwndbg | 需要动态观察输入、寄存器或内存时再用 |

## 首轮 10 分钟操作流程

### Step 1：先做基础识别

```bash
file ./chall
strings ./chall | less
```

重点找：

- `flag`、比赛前缀、`correct`、`wrong`、`success`
- `getenv`、环境变量名、`usage`、路径、URL
- 是否有明显密文、key、提示语

### Step 2：打开 Ghidra，但先看字符串

Ghidra 最小操作流：

1. 新建 Project，导入二进制。
2. 选择 Auto Analyze。
3. 打开 `Window -> Defined Strings`。
4. 搜索关键字符串，例如 `flag`、`CTF`、`wrong`、`getenv` 参数名。
5. 双击字符串，在 Listing / Decompiler 中看引用位置。
6. 从引用位置往上找主流程函数。

初学时优先看 Decompiler，不要一上来盯汇编。

### Step 3：找输入来源

常见输入来源对应的函数：

| 输入来源 | 常见函数/特征 |
|----------|---------------|
| stdin | `scanf`、`fgets`、`read` |
| 命令行参数 | `argc`、`argv` |
| 环境变量 | `getenv("NAME")` |
| 文件 | `fopen`、`read`、文件路径字符串 |
| 网络 | `recv`、`send`、socket 调用 |

例如 `Out of World` 里看到 `getenv("CTF_SECRET_KEY")`，就应该立刻判断：这题关键输入不是键盘输入，而是环境变量。

### Step 4：找校验函数

很多入门题都是这种结构：

```c
input = get_input();
if (!check(input)) {
    puts("wrong");
    return 1;
}
print_or_decode_flag(input);
```

重点看 `check`：

- 长度是否固定
- 是否逐字节循环
- 是否有 `^`、`+`、`-`、移位
- 是否和 `.rodata` / `.data` 中的数组比较

看到这种逻辑：

```c
if ((input[i] ^ 0x23) != data[i]) return 0;
```

要立刻反推：

```text
input[i] = data[i] ^ 0x23
```

### Step 5：看通过校验后做什么

校验通过后常见三种情况：

1. 直接 `puts(flag)`
2. 拼接多个字符串得到 flag
3. 用正确输入作为 key 解密 flag

`Out of World` 就是第三种：先反推出环境变量 `THIS_IS_SUPER_SECRET_KEY`，再用它循环异或密文得到 flag。

## 典型突破口

| 现象 | 优先尝试 |
|------|----------|
| `strings` 直接出现 flag 前缀 | 先确认是否唯一且完整 |
| 出现 `getenv` | 找环境变量名和校验函数 |
| 出现 `strcmp` / `memcmp` | 看参与比较的两个参数 |
| 有循环和 `^` | 抄出数组和常量，写 Python 反推 |
| 成功提示在某个分支 | 找到到达该分支的条件 |
| stripped 但函数很少 | 从字符串交叉引用定位主逻辑 |

## 新手常见误区

- 一上来就试图读懂所有汇编，结果忘了先看字符串。
- 看到 stripped 就以为很难，其实小程序仍然可以靠字符串和伪代码定位。
- 只想着 stdin，忽略了 `argv`、`getenv`、文件内容这些输入来源。
- 把“程序正向校验”看完了，却没有写出对应的“逆向恢复公式”。
- 没给函数和变量重命名，导致自己越看越乱。

## 仓库内参考阅读

- [CPCTF hidden](../Reverse Engineering(逆向工程)/CPCTF_hidden.md) — 最基础的 `file` / `strings` 初筛。
- [CPCTF Out of World](../Reverse Engineering(逆向工程)/CPCTF_Out_of_World.md) — `getenv` + Ghidra + XOR 还原的典型入门题。
- [Novruz Reverse by Zoktay](../Reverse Engineering(逆向工程)/NovruzCTF_Novruz_Reverse_by_Zoktay.md) — Ghidra 定位函数与 XOR 解码。
- [Novruz Ritual](../Reverse Engineering(逆向工程)/NovruzCTF_Novruz Ritual.md) — 更完整的 Ghidra / 工具对比示例。

## 一页式检查清单

- [ ] 用 `file` 判断了文件类型和架构
- [ ] 用 `strings` 找过 flag 前缀、提示语、成功/失败文本
- [ ] 确认了输入来源：stdin / argv / getenv / 文件 / 网络
- [ ] 在 Ghidra 里通过字符串交叉引用找到了主逻辑
- [ ] 找到了校验函数或成功分支条件
- [ ] 把关键比较逻辑写成了可逆公式
- [ ] 用 Python 或手算复现了关键变换
- [ ] 确认最终 flag 格式完整且可提交