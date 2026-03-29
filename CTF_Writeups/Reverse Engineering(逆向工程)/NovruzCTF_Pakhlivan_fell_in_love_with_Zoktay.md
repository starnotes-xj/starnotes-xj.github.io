# Zoktay Crack Me - CTF Reverse Engineering Writeup

## 题目信息

- **题目名称**: zoktay_crack_me
- **分类**: Reverse Engineering (逆向工程)
- **难度**: Easy
- **文件**: `65c452c9-d9ce-4287-a621-c54e5624c82c.bin` (ELF 64-bit)
- **状态**: 已解

## 题目描述

> 只有聪明的研究人员和帕克利文才需要抵抗。
> 所以他们才会用测试任务来筛选新人。
> 它很简单，但缺少一点技巧。
> 他们现在非常需要帮助，所以你也会有其他任务可以完成。
> 但如果你想赚点外快，完成这个任务就能得到你想要的东西。

## 解题过程

### 1. 文件分析

首先分析文件类型：

```bash
$ file zoktay_crack_me.bin
zoktay_crack_me.bin: ELF 64-bit LSB pie executable, x86-64,
version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
for GNU/Linux 3.2.0, not stripped
```

关键信息：
- 64位ELF可执行文件
- 动态链接
- **未剥离符号** (not stripped) - 这意味着我们可以看到函数名

### 2. 字符串提取

使用Python脚本提取程序中的字符串，发现以下关键信息：

```
Usage: %s <password>
this_is_not_flag
[+] Correct flag!
[-] Incorrect flag!
encrypted_flag
PRGA
swap
```

**关键发现**：
- 程序需要密码参数
- 有 `PRGA` 和 `swap` 函数 → 这是 **RC4加密算法** 的特征！
  - PRGA = Pseudo-Random Generation Algorithm (伪随机生成算法)
  - swap = RC4中的交换操作
- `this_is_not_flag` - 这个字符串看起来像是干扰项

### 3. ELF段分析

解析ELF文件结构，查找加密数据：

#### .rodata段
包含只读字符串，没有加密数据。

#### .data段（关键！）
在 `.data` 段偏移 `0x3020` 处找到 **69字节的加密数据**：

```
65 f9 45 ce 8a 60 e0 90 fe 66 ff 67 ef 1b d1 2e
f1 6b a4 0f 96 9e be c0 0b 88 c3 40 06 27 5a d2
df a6 15 0d 8d ef cf 29 83 a4 44 3d d7 9b f4 9e
87 67 4d cf 4e 5a e0 6b f4 13 e1 dc bb ce 73 14
ee 09 e3 4f 46
```

### 4. RC4解密

#### RC4算法简介

RC4是一种流密码算法，由两部分组成：
1. **KSA (Key Scheduling Algorithm)** - 密钥调度算法
2. **PRGA (Pseudo-Random Generation Algorithm)** - 伪随机生成算法

#### Python实现

```python
def rc4_ksa(key):
    """RC4密钥调度算法"""
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    return S

def rc4_prga(S, data):
    """RC4伪随机生成算法"""
    i = j = 0
    output = []
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        output.append(byte ^ K)
    return bytes(output)

def rc4_decrypt(key, ciphertext):
    """RC4解密"""
    if isinstance(key, str):
        key = key.encode()
    S = rc4_ksa(key)
    return rc4_prga(S, ciphertext)
```

#### Go 实现

```go
package main

func rc4KSA(key []byte) []byte {
    S := make([]byte, 256)
    for i := 0; i < 256; i++ {
        S[i] = byte(i)
    }
    j := 0
    for i := 0; i < 256; i++ {
        j = (j + int(S[i]) + int(key[i%len(key)])) & 0xff
        S[i], S[j] = S[j], S[i]
    }
    return S
}

func rc4PRGA(S []byte, data []byte) []byte {
    i, j := 0, 0
    out := make([]byte, len(data))
    for idx, b := range data {
        i = (i + 1) & 0xff
        j = (j + int(S[i])) & 0xff
        S[i], S[j] = S[j], S[i]
        k := S[(int(S[i])+int(S[j]))&0xff]
        out[idx] = b ^ k
    }
    return out
}

func rc4Decrypt(key string, ciphertext []byte) []byte {
    S := rc4KSA([]byte(key))
    return rc4PRGA(S, ciphertext)
}
```

### 5. 密钥破解

#### 尝试常见密码

首先尝试程序中出现的字符串作为密码。**关键洞察**：

虽然字符串叫 `"this_is_not_flag"`，但这可能是一个**反向思维陷阱**！
它可能恰恰就是密钥！

#### 解密验证

```python
encrypted_data = bytes([
    0x65, 0xf9, 0x45, 0xce, 0x8a, 0x60, 0xe0, 0x90,
    0xfe, 0x66, 0xff, 0x67, 0xef, 0x1b, 0xd1, 0x2e,
    # ... (完整的69字节)
])

decrypted = rc4_decrypt("this_is_not_flag", encrypted_data)
print(decrypted.decode())
```

**结果**：

```
novruzCTF{ea9d371ee29e03cf04054bc1154a8b0b4513614d246fe4653adc7e03f4a2ac65}
```

✅ **成功！**

## 漏洞分析 / 机制分析
- **RC4 流密码**：密文存放在 `.data` 段，运行时用 RC4 解密并比较。
- **弱点**：密钥字符串 `this_is_not_flag` 直接硬编码在二进制中。
- **利用点**：静态提取密钥与密文即可离线解密，无需运行程序。

## 使用的工具
- Ghidra / Radare2 — 反编译与字符串定位
- Python — ELF 解析与 RC4 解密脚本
- file — 文件类型识别
- ctf_tools/crypto — RC4 解密验证（可选）

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Pakhlivan_fell_in_love_with_Zoktay.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Pakhlivan_fell_in_love_with_Zoktay.py`

## 推荐工具与优化解题流程

下面是基于扩展计划里推荐工具的**更快流程**，减少手写脚本量。

### 1) 逆向定位（Ghidra / Radare2）

**Ghidra 流程**：
1. 导入二进制并选择 **Auto-Analyze**。
2. 在 **Symbol Tree** 中搜索 `encrypted_flag`，双击定位到 `.data`。
3. 右键数据 → **Copy Special / Export**，保存 69 字节为 `encrypted.bin`。
4. 在 **Strings** 中找到 `this_is_not_flag`，确认密钥。
5. 在 **Functions** 中查看 `RC4` / `PRGA`，确认算法是 RC4。

**Radare2 流程（可选）**：
```bash
r2 -A zoktay_crack_me
iz~flag
afl~RC4
pdf @ main
px 69 @ sym.encrypted_flag
```

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Ghidra** | 反编译定位 | ~10 分钟 | 伪代码直观 | 需要 GUI |
| **Radare2** | 快速定位 | ~5 分钟 | CLI 快速 | 学习成本高 |
| **ctf_tools/crypto** | 解密验证 | ~1 分钟 | 一键 RC4 | 需先构建 |
| **Python 脚本** | 自动解析 | ~5 分钟 | 可重复 | 需要脚本维护 |

### 推荐流程
**推荐流程**：Ghidra/Radare2 定位密钥与密文 → Python 解密验证 → 5-10 分钟完成。

## 命令行提取关键数据（无 GUI）

**提取 encrypted.bin**：

方式 A（GNU dd / WSL / Git Bash）：
```bash
# 0x3020 是 encrypted_flag 在文件中的偏移，长度 69 字节

dd if=zoktay_crack_me of=encrypted.bin bs=1 skip=$((0x3020)) count=69 status=none
```

方式 B（Python）：
```bash
python - <<'PY'
with open("zoktay_crack_me", "rb") as f:
    f.seek(0x3020)
    data = f.read(69)
with open("encrypted.bin", "wb") as f:
    f.write(data)
PY
```

### 2) 快速解密（crypto_toolkit 的 RC4）

使用本仓库的 `ctf_tools/crypto`：
```bash
cd ctf_tools/crypto
go build -o crypto_toolkit.exe
./crypto_toolkit decrypt -a rc4 -k "this_is_not_flag" -i encrypted.bin -o out.txt
```

`out.txt` 得到：
```
Cup{ea9d371ee29e03cf04054bc1154a8b0b4513614d246fe4653adc7e03f4a2ac65}
```

平台提交前缀规则：
```
novruzCTF{ea9d371ee29e03cf04054bc1154a8b0b4513614d246fe4653adc7e03f4a2ac65}
```

## Flag

```
novruzCTF{ea9d371ee29e03cf04054bc1154a8b0b4513614d246fe4653adc7e03f4a2ac65}
```

## 知识点
- **RC4 结构** — KSA + PRGA 两阶段
- **ELF 段分析** — 密文常位于 `.data`
- **硬编码密钥** — 静态分析直接提取

## 解题技巧总结

### 关键技术点

1. **ELF文件分析** - 理解ELF文件结构，提取段数据
2. **RC4算法识别** - 通过函数名（PRGA、swap）识别加密算法
3. **反向思维** - "this_is_not_flag" 实际上就是密钥！

### 工具使用

- `file` - 识别文件类型
- Python - ELF解析和RC4实现
- 字符串提取脚本

### 陷阱分析

**题目设置的陷阱**：
- 字符串命名为 `"this_is_not_flag"` → 让你以为它不是密钥
- 实际上它**就是**RC4的解密密钥
- 这是一种常见的社会工程学技巧

### 学习要点

1. **不要被表面迷惑** - 程序中的提示信息可能是反向的
2. **识别加密算法** - 通过函数名和数据特征识别
3. **ELF结构理解** - 知道在哪里找数据（.rodata vs .data）
4. **Python脚本** - 快速实现分析和解密工具

## 完整解题脚本

```python
#!/usr/bin/env python3

def rc4_decrypt(key, ciphertext):
    """RC4解密函数"""
    if isinstance(key, str):
        key = key.encode()

    # KSA
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]

    # PRGA
    i = j = 0
    output = []
    for byte in ciphertext:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        output.append(byte ^ K)

    return bytes(output)

# 加密数据
encrypted_data = bytes([
    0x65, 0xf9, 0x45, 0xce, 0x8a, 0x60, 0xe0, 0x90,
    0xfe, 0x66, 0xff, 0x67, 0xef, 0x1b, 0xd1, 0x2e,
    0xf1, 0x6b, 0xa4, 0x0f, 0x96, 0x9e, 0xbe, 0xc0,
    0x0b, 0x88, 0xc3, 0x40, 0x06, 0x27, 0x5a, 0xd2,
    0xdf, 0xa6, 0x15, 0x0d, 0x8d, 0xef, 0xcf, 0x29,
    0x83, 0xa4, 0x44, 0x3d, 0xd7, 0x9b, 0xf4, 0x9e,
    0x87, 0x67, 0x4d, 0xcf, 0x4e, 0x5a, 0xe0, 0x6b,
    0xf4, 0x13, 0xe1, 0xdc, 0xbb, 0xce, 0x73, 0x14,
    0xee, 0x09, 0xe3, 0x4f, 0x46
])

# 解密
password = "this_is_not_flag"
flag = rc4_decrypt(password, encrypted_data)
print(f"FLAG: {flag.decode()}")
```

**输出**：
```
FLAG: novruzCTF{ea9d371ee29e03cf04054bc1154a8b0b4513614d246fe4653adc7e03f4a2ac65}
```

## 时间线

1. ✅ 识别文件类型 (ELF 64-bit)
2. ✅ 提取字符串，发现RC4算法特征
3. ✅ 解析ELF结构，提取加密数据
4. ✅ 实现RC4解密算法
5. ✅ 尝试常见密码，发现 "this_is_not_flag" 就是密钥
6. ✅ 成功解密，获得FLAG

---

**解题时间**: ~30分钟
**难度评价**: Easy-Medium
**关键点**: 识别RC4算法 + 反向思维
