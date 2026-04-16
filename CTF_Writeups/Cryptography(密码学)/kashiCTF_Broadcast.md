# kashiCTF 2026 - Broadcast Writeup

## 题目信息

- **比赛**: kashiCTF 2026
- **题目**: Broadcast
- **类别**: Crypto
- **难度**: 简单
- **附件**: `output (1).txt`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Broadcast/output.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Broadcast){target="_blank"}
- **Flag格式**: `kashiCTF{...}`
- **状态**: 已解

## Flag

```text
kashiCTF{h4st4d_s4ys_sm4ll_3xp0n3nts_k1ll_RSA_br04dc4sts}
```

## 解题过程

### 1. 分析题目描述与附件

题目描述："为了确保冗余，我们向三台服务器发送了相同的公告。每台服务器都有自己的 RSA 密钥。截获这三份公告——或许你能从中拼凑出一些线索。"

`output (1).txt` 包含以下结构：

| 参数 | 说明 |
|------|------|
| $e$ | 3（极小的公钥指数） |
| $n_1, n_2, n_3$ | 三个不同的 RSA 模数（均为 1024 位量级） |
| $c_1, c_2, c_3$ | 三份密文（**完全相同**） |

关键观察：

- **e = 3**：极小的公钥指数，典型的 Hastad 广播攻击目标
- **三份密文完全一致**：说明 $m^3 < \min(n_1, n_2, n_3)$，加密过程中没有发生模约减

### 2. 识别攻击方式：Hastad 广播攻击

在标准的 Hastad 广播攻击中，同一明文 $m$ 用相同的小指数 $e$ 对不同模数加密，需要通过中国剩余定理（CRT）组合 $e$ 组密文来恢复 $m^e$，然后开 $e$ 次方根。

但本题更简单——三份密文 $c_1 = c_2 = c_3$ 完全相同，这意味着：

$$c = m^3 \bmod n_i \quad (i = 1, 2, 3)$$

由于 $c$ 值相同且远小于任何 $n_i$，可以确定 $m^3 = c$（精确等式，无模运算）。只需对 $c$ 计算**整数立方根**即可。

### 3. 计算整数立方根

对密文 $c$ 使用二分法求精确整数立方根：

```go
// 二分查找 m，使得 m^3 = c
lo, hi := 0, c
for lo < hi {
    mid := (lo + hi + 1) / 2
    if mid^3 <= c {
        lo = mid
    } else {
        hi = mid - 1
    }
}
// lo^3 == c，验证通过
```

### 4. 获取 Flag

立方根 $m$ 的大整数字节表示直接解码为 ASCII 字符串：

```text
kashiCTF{h4st4d_s4ys_sm4ll_3xp0n3nts_k1ll_RSA_br04dc4sts}
```

## 攻击链/解题流程总结

```text
识别 e=3 + 三密文相同 → 确认 m^3 = c（无模约减） → 整数立方根 → Flag
```

## 漏洞分析 / 机制分析

### 根因

- **公钥指数 e 过小**（e=3），导致 $m^e$ 可能小于模数 $n$，密文不受模运算保护
- **相同明文广播给多个接收者**，不使用随机填充（如 OAEP），使得 Hastad 攻击成为可能
- 本题中 $m^3 < n$，甚至不需要 CRT，直接开根即可

### 影响

- 攻击者截获任意一份密文即可恢复完整明文
- 无需分解任何 RSA 模数，计算复杂度极低（仅一次二分查找）

### 修复建议

- 使用标准填充方案（OAEP），在加密前引入随机性，使相同明文每次产生不同密文
- 使用标准公钥指数 $e = 65537$，确保 $m^e \gg n$
- 避免将未填充的原始消息直接广播给多个接收者

## 知识点

- **Hastad 广播攻击**：同一消息用相同小指数 $e$ 加密并发送给 $e$ 个或更多接收者时，可通过 CRT + 开 $e$ 次根恢复明文
- **RSA 小指数风险**：$e$ 过小且无填充时，$m^e$ 可能不超过 $n$，密文失去安全性
- **中国剩余定理（CRT）**：经典的 Hastad 攻击需要 CRT 合并多组同余方程；本题因密文相同而简化
- **整数 $k$ 次根**：大整数的精确整数根计算，常用二分法或 Newton 迭代

## 使用的工具

- Go `math/big` — 大整数运算与整数立方根计算
- **Security MCP Hub** — `crypto_iroot` / `crypto_rsa_hastad` 一键求解

## 脚本归档

- Go：[`kashiCTF_Broadcast.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/kashiCTF_Broadcast.go){target="_blank"}
- Python：[`kashiCTF_Broadcast.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/kashiCTF_Broadcast.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 使用 Go 直接求解
go run kashiCTF_Broadcast.go
# 输出: kashiCTF{h4st4d_s4ys_sm4ll_3xp0n3nts_k1ll_RSA_br04dc4sts}
```

## MCP 工具解法（Security MCP Hub）

本题可通过 [security-mcp-hub](https://github.com/starnotes-xj/security-mcp-hub) 项目提供的 Crypto MCP 工具**零代码**求解，无需编写任何脚本。

### 方法一：`crypto_iroot` — 整数立方根

由于三份密文完全相同（$c_1 = c_2 = c_3 = c$），确认 $m^3 = c$（无模约减），直接对 $c$ 求整数立方根：

```
调用: crypto_iroot(n=<密文c>, k=3)

返回:
{
  "is_exact": true,
  "root": "780484271864688109...85565",
  "root_hex": "0x6b617368694354467b...7d"
}
```

`is_exact: true` 确认 $c$ 是精确的完全立方数。将 `root_hex` 解码为 ASCII 即得 Flag。

### 方法二：`crypto_rsa_hastad` — Håstad 广播攻击一键求解

即使三份密文不同（标准 Håstad 场景），也可使用该工具，它内部自动完成 CRT + 开 $e$ 次根：

```
调用: crypto_rsa_hastad(
  pairs=[
    {"c": "<c1>", "n": "<n1>"},
    {"c": "<c2>", "n": "<n2>"},
    {"c": "<c3>", "n": "<n3>"}
  ],
  e=3
)

返回:
{
  "plaintext_hex": "0x6b617368694354467b...7d",
  "plaintext_bytes": "6b61736869...7d"
}
```

`plaintext_bytes` 十六进制解码即为 Flag：

```text
kashiCTF{h4st4d_s4ys_sm4ll_3xp0n3nts_k1ll_RSA_br04dc4sts}
```

### MCP 解题优势

- **零代码**：无需编写 Go/Python 脚本，直接在 Claude Code / MCP 客户端中调用工具
- **即时验证**：`is_exact: true` 自动验证结果正确性
- **双重方法**：`crypto_iroot` 适合简化场景（密文相同），`crypto_rsa_hastad` 覆盖通用 Håstad 场景

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 优点 | 缺点 |
|------|----------|------|------|
| **Security MCP Hub** | 求解 | 零代码，`crypto_rsa_hastad` 一键完成 | 需配置 MCP 服务 |
| Go math/big | 求解 | 标准库即可，无需额外依赖 | 需手写二分法 |
| Python gmpy2 | 求解 | `iroot()` 一行搞定 | 需安装 gmpy2 |
| SageMath | 分析+求解 | 数学函数丰富 | 环境较重 |

### 推荐流程

**推荐流程**：识别 e=3 广播模式 → MCP `crypto_rsa_hastad` 一键求解 → Flag（< 10 秒）。
