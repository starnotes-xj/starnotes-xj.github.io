# Hack For A Change 2026 March - Encrypted Audit Logs Writeup

## 题目信息

- **比赛**: Hack For A Change 2026 March (UN SDG3)
- **题目**: Encrypted Audit Logs
- **类别**: Crypto
- **难度**: 简单
- **题目描述**: Decrypt tampered audit log entries to reconstruct evidence of unauthorized access.
- **附件**: `Encrypted_Audit_Logs.txt`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Encrypted_Audit_Logs/Encrypted_Audit_Logs.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Encrypted_Audit_Logs){target="_blank"}
- **Flag格式**: `SDG{...}`
- **状态**: 已解

## Flag

```text
SDG{0a8ab0e5e0b798f6f59e4bb046e0eb71}
```

## 解题过程

### 1. 审计日志分析

附件是一份医疗系统 ClinCore Health Systems 的审计日志导出，包含 2026-03-15 至 2026-03-17 三天的系统记录。日志中散布着多个 Base32 编码的 `EncryptedToken`。

提取所有 token：

| 行号 | 上下文 | Token |
|------|--------|-------|
| 12 | 自检 | `ORSXG5A=` |
| 16 | 快照 | `QMFYHA3BPJZWKYLOM5XGC3TPNRSWM===` |
| 22 | alice 操作 | `ONSWG4TFORQXIIDBNZSCAZLPON2XGYLSMUQHG43JMRPWK3TFFQQCK2LFNYQQ====` |
| 39 | 数据导出 | `NRQWKZLBNZXWY3LTNFSW45DFMVZWKZLSOR3WKIDPMQQHK3TLMRSA4TBGRSAX====` |
| 61 | 密钥轮换 | `ONSWG4TFORQXIIDBNZSCAZDPNR2WM===` |
| 77 | 链验证 | `PFZWK3TFONRWGZLOMFQWC5LBNZ2WY4TFORXXIIDJNZSCA4DPOJSS2ZLFNRSA====` |
| **108** | **会话检查点** | **`LHHPPHR25OEII2F22XIG7OWS2IZ3FVWTNS7YTAB65DJNKPV42XKW72EH2R3Q====`** |

第 12 行的自检给出了验证：`ORSXG5A=` Base32 解码为 `test`，确认 token 使用 Base32 编码。

### 2. 识别异常 token

对所有 token 进行 Base32 解码：

```python
import base64
# 大部分 token 解码为可读 ASCII
base64.b32decode("ONSWG4TFORQXIIDBNZSCAZDPNR2WM===")
# => b'secret_data_upload'  (可读)

# 第 108 行解码为非 ASCII 乱码
base64.b32decode("LHHPPHR25OEII2F22XIG7OWS2IZ3FVWTNS7YTAB65DJNKPV42XKW72EH2R3Q====")
# => b'\x59\xce\xf7\x9e\x3a\xeb\x88\x84...'  (二进制数据!)
```

**第 108 行的 token 是唯一解码为非 ASCII 的**——这就是被篡改/加密的条目。

### 3. 发现加密配置 — XOR 重复密钥

日志第 62 行明确记录了加密配置：

```text
[2026-03-15 16:00:05] ENCRYPT: Cipher config: XOR mode=repeating key_len=4
```

**关键信息**：使用 4 字节重复密钥的 XOR 加密。

### 4. 已知明文攻击 — 恢复密钥

Flag 格式为 `SDG{`，恰好 **4 字节 = 密钥长度**，可以直接通过已知明文攻击恢复密钥：

$$\text{key}[i] = \text{ciphertext}[i] \oplus \text{plaintext}[i], \quad i \in \{0,1,2,3\}$$

```text
ciphertext[0:4] = 0x59 0xCE 0xF7 0x9E
plaintext[0:4]  = 'S'  'D'  'G'  '{'  = 0x53 0x44 0x47 0x7B
key             = 0x0A 0x8A 0xB0 0xE5
```

用密钥 `0x0A8AB0E5` 解密全部 37 字节密文：

```text
SDG{0a8ab0e5e0b798f6f59e4bb046e0eb71}
```

## 攻击链/解题流程总结

```text
审计日志分析 → 提取 Base32 token → 识别非 ASCII 异常条目 (L108) → 发现 XOR key_len=4 配置 (L62) → 已知明文 "SDG{" 恢复密钥 → XOR 解密 → Flag
```

## 漏洞分析

### 根因

- **XOR 加密本身不安全**：XOR 是对称的、无扩散的，密钥可通过已知明文直接恢复
- **密钥长度过短**：4 字节密钥仅 $2^{32}$ 种可能，即使没有已知明文也可暴力破解
- **加密配置写入明文日志**：攻击者可直接从日志获取加密算法和密钥长度

### 影响

审计日志中的篡改记录（未授权访问证据）可被完整还原，XOR "加密"未提供任何实质保护。

### 修复建议

- 使用 AES-GCM 等认证加密算法保护敏感日志条目
- 不要在明文日志中记录加密配置参数
- 对审计日志实施写后不可篡改（append-only）策略

## 知识点

- **Base32 编码** — RFC 4648 标准编码，使用 A-Z 和 2-7，padding 用 `=`
- **XOR 加密** — 最简单的对称加密，$C = P \oplus K$，$P = C \oplus K$
- **已知明文攻击 (Known-Plaintext Attack)** — 当攻击者知道部分明文时，可直接恢复密钥
- **重复密钥 XOR 的弱点** — 密钥长度 $\leq$ 已知明文长度时，密钥可被完全恢复

## 使用的工具

- **Python `base64`** — Base32 解码
- **Python 字节运算** — XOR 解密

## 脚本归档

- Go：[`HackForAChange2026March_UN_SDG3_Encrypted_Audit_Logs.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/HackForAChange2026March_UN_SDG3_Encrypted_Audit_Logs.go){target="_blank"}
- Python：[`HackForAChange2026March_UN_SDG3_Encrypted_Audit_Logs.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/HackForAChange2026March_UN_SDG3_Encrypted_Audit_Logs.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 一行 Python 解题
python3 -c "
import base64
ct = base64.b32decode('LHHPPHR25OEII2F22XIG7OWS2IZ3FVWTNS7YTAB65DJNKPV42XKW72EH2R3Q====')
key = bytes([ct[i]^b'SDG{'[i] for i in range(4)])
print(bytes([ct[i]^key[i%4] for i in range(len(ct))]).decode())
"
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Crypto 工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Python** | 解码 + 解密 | ~1 秒 | 一行脚本解决 | 无 |
| **CyberChef** | 可视化解码 | ~30 秒 | 拖拽操作，直观 | 需手动拼接步骤 |
| **xortool** | XOR 分析 | ~5 秒 | 自动推断密钥长度 | 本题已知密钥长度，无需 |

### 推荐流程

**推荐流程**：`grep` 提取 token → Base32 解码识别异常 → 读取 XOR 配置 → 已知明文恢复密钥 → 解密（~30 秒）。

### CyberChef（可视化方案）

**配方**：`From Base32` → `XOR` (Key: `0a8ab0e5`, Hex)

直接粘贴 Base32 token，设置 XOR key 为 `0a8ab0e5`（Hex 格式），即可看到 flag。
