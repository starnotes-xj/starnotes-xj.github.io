# kashiCTF 2026 - Secret of Mahabharata Writeup

## 题目信息

- **比赛**: kashiCTF 2026
- **题目**: Secret of Mahabharata
- **类别**: Crypto
- **难度**: 简单
- **题目描述**:
    - 原文: 自伟大的摩诃婆罗多大战以来，一条秘密信息便代代相传。传说每隔64年，守护这条秘密的人都会重新加密信息，以防有人滥用其力量。这条信息已历经3136年的历史，从公元前3136年的俱卢之野战场一直流传到公元纪元之初。
    - 提交前请尝试将 flag 格式更改为 kashiCTF {...}。
- **附件**: `secret_message.txt`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Secret_of_Mahabharata/secret_message.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Secret_of_Mahabharata){target="_blank"}
- **Flag格式**: kashiCTF{...}
- **状态**: 已解

## Flag

```text
kashiCTF{th3_s3cr3t_0f_mah4bh4r4t4_fr0m_3136_BCE}
```

## 解题过程

### 1. 分析题目信息

题目描述中包含关键数值：

| 信息 | 含义 |
|------|------|
| 每隔 **64** 年重新加密 | 暗示 **Base64** 编码 |
| 历经 **3136** 年 | 总时间跨度 |
| 3136 ÷ 64 = **49** | 编码总次数 |

打开附件 `secret_message.txt`，文件大小约 **59 MB**，内容为纯 Base64 字符串（`Vm0wd2QyUXlVWGxW...`），无换行、无其他格式——典型的多层 Base64 编码特征。

### 2. 计算编码层数

从题目描述直接计算：

$$
\text{编码次数} = \frac{3136}{64} = 49 \text{ 次}
$$

每次 Base64 编码会使数据膨胀约 $\frac{4}{3}$ 倍。反过来，49 次解码后数据量会急剧缩小：

- 第 1 次解码：59 MB → ~44 MB
- 第 10 次解码：~3.4 MB
- 第 25 次解码：~46 KB
- 第 49 次解码：**45 bytes**（最终明文）

### 3. 循环解码获取 Flag

使用 shell 脚本循环解码 49 次：

```bash
cp secret_message.txt /tmp/msg.txt
for i in $(seq 1 49); do
    base64 -d /tmp/msg.txt > /tmp/msg_dec.txt
    mv /tmp/msg_dec.txt /tmp/msg.txt
done
cat /tmp/msg.txt
```

输出结果：

```text
flag{th3_s3cr3t_0f_mah4bh4r4t4_fr0m_3136_BCE}
```

### 4. 转换 Flag 格式

根据题目要求，将 `flag{...}` 格式改为 `kashiCTF{...}`：

```text
kashiCTF{th3_s3cr3t_0f_mah4bh4r4t4_fr0m_3136_BCE}
```

## 攻击链/解题流程总结

```text
题目描述提取关键数字(64/3136) → 计算编码次数(49次) → 循环 Base64 解码 → 替换 flag 格式 → Flag
```

## 漏洞分析 / 机制分析

### 根因

- 利用 Base64 编码的**可逆性**与**无密钥特性**，多次编码并不增加安全性，只是增加数据体积
- 题目通过历史故事暗示编码方式（64 → Base64）和编码次数（3136 ÷ 64 = 49）

### 影响

- Base64 是编码而非加密，无论嵌套多少层都可以无密钥还原原文
- 唯一的"保护"是文件体积膨胀（45 bytes 原文膨胀到约 59 MB）

## 知识点

- **Base64 编码**：每次编码将 3 字节映射为 4 个 ASCII 字符，数据膨胀约 33%
- **编码 vs 加密**：Base64 是可逆编码，不提供任何安全性保障；多层编码不等于加密
- **CTF 题目信息提取**：题目描述中的数字（64、3136）通常是解题关键线索

## 使用的工具

- **base64** (coreutils) — 命令行 Base64 解码
- **Go / Python** — 编写自动化循环解码脚本

## 脚本归档

- Go：[`kashiCTF_Secret_of_Mahabharata.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/kashiCTF_Secret_of_Mahabharata.go){target="_blank"}
- Python：[`kashiCTF_Secret_of_Mahabharata.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/kashiCTF_Secret_of_Mahabharata.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 一行命令循环解码 49 次 Base64
cp secret_message.txt /tmp/msg.txt && for i in $(seq 1 49); do base64 -d /tmp/msg.txt > /tmp/msg_dec.txt && mv /tmp/msg_dec.txt /tmp/msg.txt; done && cat /tmp/msg.txt
```
