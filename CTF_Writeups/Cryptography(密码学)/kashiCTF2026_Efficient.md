# kashiCTF 2026 - Efficient Writeup

## 题目信息

- **比赛**: kashiCTF 2026
- **题目**: Efficient
- **类别**: Crypto
- **难度**: 简单
- **附件**: `output.txt`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Efficient/output.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Efficient){target="_blank"}
- **Flag格式**: `kashiCTF{...}`
- **状态**: 已解

## Flag

```text
kashiCTF{wh3n_0n3_pr1m3_1s_n0t_3n0ugh_p_squared_1s_w0rs3}
```

## 解题过程

### 1. 分析题目描述与附件

题目描述："生成素数成本很高。我优化了密钥生成方法，速度提高了一倍。模数为 4096 位——绝对安全。"

`output.txt` 包含以下结构：

| 参数 | 说明 |
|------|------|
| $n$ | 4096 位 RSA 模数 |
| $e$ | 65537（标准公钥指数） |
| `ct` | RSA 密文（Base64 编码，512 字节） |
| `iv` + `flag_ct` | AES-CBC 对称加密层（加密 flag） |
| `ct2` | 辅助密文（4095 位整数） |

**关键线索**："速度提高了一倍"意味着只生成了一个素数，然后 $n = p^2$（即 $p = q$）。

### 2. 验证 $n = p^2$ 并分解

对 $n$ 开平方根即可得到 $p$：

```python
from math import isqrt
p = isqrt(n)
assert p * p == n  # 验证通过
```

$n$ 是一个完全平方数，0 次迭代即分解成功。$p$ 为 2048 位素数。

### 3. RSA 解密得到 AES 密钥

当 $n = p^2$ 时，欧拉函数为：

$$\varphi(n) = \varphi(p^2) = p \cdot (p - 1)$$

计算私钥 $d$ 并解密 RSA 密文：

```python
phi = p * (p - 1)
d = pow(e, -1, phi)

ct_int = int.from_bytes(base64.b64decode(ct_b64), 'big')
pt_int = pow(ct_int, d, n)
pt_bytes = pt_int.to_bytes(512, 'big')
```

解密后的明文去除前导零后，最后 16 字节即为 AES 密钥：

```text
AES Key: 3a59a95d070450f5f1c070743cc7aa37
```

### 4. AES-CBC 解密获取 Flag

使用提取的 AES 密钥和附件中的 IV，以 CBC 模式解密 `flag_ct`：

```python
iv = base64.b64decode(iv_b64)
flag_ct = base64.b64decode(flag_ct_b64)
aes_key = pt_bytes[-16:]  # 最后 16 字节

cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
flag = unpad(cipher_aes.decrypt(flag_ct), 16)
# b'kashiCTF{wh3n_0n3_pr1m3_1s_n0t_3n0ugh_p_squared_1s_w0rs3}'
```

## 攻击链/解题流程总结

```text
识别 "速度提高一倍" 暗示 p=q → isqrt(n) 分解 → φ(p²)=p(p-1) 求私钥 d → RSA 解密 ct 得 AES 密钥 → AES-CBC 解密 flag_ct → Flag
```

## 漏洞分析

### 根因

- **$p = q$（重复使用同一素数）**：$n = p^2$ 不是两个不同素数之积，直接开平方即可分解，完全绕过 RSA 的安全假设
- **"优化"破坏安全性**：省略第二个素数的生成看似提升了效率，实际上消除了大整数分解的困难性

### 影响

攻击者无需任何高级分解算法，仅需一次整数平方根运算（$O(\log^2 n)$）即可分解 4096 位模数，进而解密所有密文。

### 修复建议

- **使用两个独立的大素数**：$p$ 和 $q$ 必须独立随机生成，且 $|p - q|$ 应足够大
- 使用经过安全审计的密钥生成库（如 OpenSSL），不要自行"优化"
- 对生成的密钥进行合规检查：验证 $p \neq q$、$\gcd(p-1, e) = 1$ 等

## 知识点

- **RSA 安全假设** — RSA 的安全性依赖于两个大素数之积难以分解；$p = q$ 时假设不成立
- **欧拉函数 $\varphi(p^k)$** — 对素数幂 $p^k$，$\varphi(p^k) = p^{k-1}(p-1)$；本题 $k=2$ 时 $\varphi(p^2) = p(p-1)$
- **RSA 混合加密** — 用 RSA 加密对称密钥（AES），再用对称密钥加密实际数据，是标准的混合加密方案
- **费马分解法** — 当 $p$ 和 $q$ 接近时（极端情况：$p = q$），可通过 $a^2 - n = b^2$ 快速分解

## 使用的工具

- **Python + PyCryptodome** — RSA 解密与 AES-CBC 解密
- **math.isqrt** — Python 内置整数平方根，用于分解 $n = p^2$
- **Security MCP Hub** — `crypto_iroot` 分解 $n = p^2$，`crypto_mod_math` 辅助模运算

## 脚本归档

- Python：[`kashiCTF2026_Efficient.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/kashiCTF2026_Efficient.py){target="_blank"}
- 说明：完整解题脚本，包含分解、RSA 解密、AES 解密全流程

## 命令行提取关键数据（无 GUI）

```bash
# 一键求解（需安装 pycryptodome）
python kashiCTF2026_Efficient.py
```

## MCP 工具解法（Security MCP Hub）

本题可通过 [security-mcp-hub](https://github.com/starnotes-xj/security-mcp-hub) 项目提供的 Crypto MCP 工具完成**关键分解步骤**，后续 AES 解密配合 `cyberchef_decrypt` 完成。

### 步骤一：`crypto_iroot` — 分解 $n = p^2$

对 4096 位 RSA 模数 $n$ 开平方根，验证是否为完全平方数：

```
调用: crypto_iroot(n=0x752a94a1...59479, k=2)

返回:
{
  "is_exact": true,
  "root": "218631407806408676...56843",
  "root_hex": "0xad307ed8fa74c548...0b"
}
```

`is_exact: true` 确认 $n$ 是完全平方数，`root` 即为素数 $p$（2048 位）。这一步零代码完成了分解，无需编写任何脚本。

### 步骤二：`crypto_mod_math` — 计算 RSA 私钥

使用模逆运算求私钥 $d = e^{-1} \mod \varphi(p^2)$：

```
调用: crypto_mod_math(
  operation="inverse",
  a="65537",
  b="<φ(n) = p*(p-1)>",
  m="<φ(n)>"
)
```

### 步骤三：RSA 解密 + AES-CBC 解密

RSA 解密得到 AES 密钥后，使用 `cyberchef_decrypt` 完成 AES-CBC 解密：

```
调用: cyberchef_decrypt(
  data="<flag_ct hex>",
  algorithm="aes-cbc",
  key="3a59a95d070450f5f1c070743cc7aa37",
  iv="5d20a7a592f237639a9fb17aee138a59"
)
```

最终得到 Flag：

```text
kashiCTF{wh3n_0n3_pr1m3_1s_n0t_3n0ugh_p_squared_1s_w0rs3}
```

### MCP 解题优势

- **即时分解**：`crypto_iroot` 对 4096 位模数开平方根，`is_exact: true` 自动验证完全平方数
- **模块化流程**：分解（`crypto_iroot`）→ 模运算（`crypto_mod_math`）→ 解密（`cyberchef_decrypt`），每步独立可验证
- **混合加密覆盖**：Crypto MCP 处理 RSA 数论层，CyberChef MCP 处理 AES 对称层，工具链完整

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Crypto 工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Security MCP Hub** | 分解 + 模运算 | < 1 秒 | 零代码分解，即时验证完全平方数 | AES 层需配合 CyberChef |
| **Python + PyCryptodome** | 全流程 | < 1 秒 | 灵活，可处理混合加密 | 需手动编写逻辑 |
| **RsaCtfTool** | RSA 分析 | 即时 | 自动检测 p=q 等弱点 | 不处理后续 AES 层 |
| **SageMath** | 数论分析 | 即时 | 内置 `is_square()` 等函数 | 对本题杀鸡用牛刀 |

### 推荐流程

**推荐流程**：MCP `crypto_iroot` 分解 $n = p^2$ → `crypto_mod_math` 求私钥 → RSA 解密得 AES 密钥 → `cyberchef_decrypt` 解密 → Flag（< 30 秒）。

### Python + PyCryptodome（脚本方案）

- **安装**：`pip install pycryptodome`
- **详细步骤**：
  1. 从 `output.txt` 提取 $n$、$e$、密文、IV 等参数
  2. `isqrt(n)` 计算 $p$，验证 $p^2 = n$
  3. 计算 $\varphi(n) = p(p-1)$，求 $d = e^{-1} \mod \varphi(n)$
  4. RSA 解密 `ct` 得到 AES 密钥，AES-CBC 解密 `flag_ct` 得到 flag
- **优势**：一个脚本搞定全部流程，无需额外依赖

### RsaCtfTool（可选）

- **安装**：`git clone https://github.com/RsaCtfTool/RsaCtfTool.git`
- **详细步骤**：可自动检测 $n$ 为完全平方数并分解，但后续 AES 解密层仍需手动处理
- **优势**：快速识别 RSA 弱点类型
