---
title: Pwn 新手上手操作指南
---

# Pwn 新手上手操作指南

Pwn 入门不要一开始就想复杂 ROP。先确认文件类型、保护机制、交互方式和最短可达目标。很多入门题只需要 ret2win、格式化字符串泄漏/写入，或一个很小的业务逻辑漏洞。

## 这类题先看什么

先确认：

1. 题目给的是本地二进制、源码、Docker，还是远程服务？
2. 架构是什么？32 位/64 位，ELF/PIE，动态/静态链接？
3. 开了哪些保护？Canary、NX、PIE、RELRO？
4. 能控制什么输入？长度、格式、次数、菜单项？
5. 目标是什么？调用 win 函数、泄漏地址、改 GOT、拿 shell，还是绕过业务逻辑？

## 最小工具集

| 工具 | 用途 |
|------|------|
| `file` | 判断架构和文件类型 |
| `checksec` | 查看保护机制 |
| `strings` | 找菜单、提示、`/bin/sh`、win 函数线索 |
| Ghidra / IDA | 看主流程和危险函数 |
| gdb + pwndbg | 动态调试、确认偏移、观察崩溃 |
| pwntools | 编写最终利用脚本 |

## 首轮 10 分钟操作流程

### Step 1：基础识别

```bash
file ./chall
checksec ./chall
strings ./chall | less
```

重点看：

- 有没有 `win`、`backdoor`、`flag`、`/bin/sh`
- 有没有菜单和输入提示
- 是否 stripped
- 保护机制决定利用路线

### Step 2：本地跑一遍

```bash
./chall
```

记录：

- 输入点有几个
- 每个输入长度是否有限制
- 是否能重复输入
- 是否会回显
- 崩溃是否容易触发

### Step 3：找危险函数和控制点

在反编译器或源码中重点看：

- `gets`、`scanf("%s")`、`read` 长度过大
- `printf(user_input)` 格式化字符串
- 数组越界、整数溢出、菜单索引未检查
- `system`、`execve`、`puts`、`printf` 等可利用调用

### Step 4：先构造最短利用链

| 现象 | 入门路线 |
|------|----------|
| 有 win 函数且可溢出返回地址 | ret2win |
| NX 关 | shellcode 可能可行 |
| 有格式化字符串 | 泄漏地址或任意写 |
| PIE 开但有泄漏 | 先算基址再跳转 |
| Canary 开且无泄漏 | 先找绕过或别的漏洞 |
| 菜单逻辑有问题 | 先利用业务逻辑，不急着 ROP |

## 典型突破口

- 返回地址偏移可控，且有现成 win 函数。
- 格式化字符串能泄漏栈、libc 或 PIE 地址。
- GOT 可写且 Partial RELRO。
- 程序提供 puts/printf 泄漏原语。
- 菜单索引未校验导致越界读写。
- 远程环境和本地 libc 不同，需要泄漏后动态计算。

## 新手常见误区

- 不看 `checksec` 就开始写 payload。
- 一上来写复杂 ROP，忽略了现成 win 函数或业务逻辑漏洞。
- 偏移没用 cyclic 确认，靠猜长度。
- 本地能打通但没考虑远程 libc、PIE、ASLR 差异。
- 没把交互封装成 pwntools 脚本，手动输入无法稳定复现。

## 仓库内参考阅读

- [CPCTF killionaire](../Pwn/CPCTF_killionaire.md) — CPCTF Pwn 入门题。
- [MetaCTF pwnMe](../Pwn/MetaCTF_pwnMe.md) — 基础栈溢出 / ret2win 思路。
- [MetaCTF Teaching Bricks](../Pwn/MetaCTF_Teaching_Bricks.md) — Pwn 基础流程参考。
- [putcCTF P2P Secure Chat](../Pwn/putcCTF_P2P_Secure_Chat.md) — 协议交互与漏洞利用链。

## 一页式检查清单

- [ ] 用 `file` 确认架构和位数
- [ ] 用 `checksec` 记录保护机制
- [ ] 本地运行并记录所有输入点
- [ ] 找到危险函数或逻辑漏洞位置
- [ ] 用 cyclic / gdb 确认偏移，不靠猜
- [ ] 判断最短利用链：ret2win / fmtstr / ROP / 逻辑漏洞
- [ ] 若远程利用，处理 libc、PIE、ASLR 差异
- [ ] 用 pwntools 写成可复现脚本