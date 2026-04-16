# putcCTF - Exercise Writeup

## 题目信息
- **比赛**: putcCTF
- **题目**: Exercise
- **类别**: Crypto
- **难度**: 简单
- **附件/URL**: `exercise.txt` · [Challenge](https://ctf.putcyberdays.pl/challenges){target="_blank"}
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Exercise/exercise.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Exercise){target="_blank"}
- **CTFtime**: [Event #3202](https://ctftime.org/event/3202/){target="_blank"}
- **Flag格式**: `putcCTF{...}`
- **状态**: 已解

## Flag

```text
putcCTF{try_br3ak1ng_0ut}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点：附件 `exercise.txt`
- 附件给出标准 RSA 参数：`n`、`e=6`、`c`
- 题目提示：`m^e` 只比 `n` 稍大（slightly larger than n）

### 2. 关键突破点一
- 当公钥指数较小（本题 `e=6`）且明文幂仅略大于模数时，可写成：

$$
 m^e = c + k\cdot n
$$

- 其中 `k` 为较小整数。问题转化为：遍历小范围 `k`，判断 `c + k*n` 是否为**完美六次幂**。

### 3. 关键突破点二
- 使用 `security-hub` MCP 的 `crypto_rsa_low_exponent`，设置：
  - `e = 6`
  - `max_k = 5000000`
- 工具命中后返回：
  - `plaintext_hex = 0x707574634354467b7472795f627233616b316e675f3075747d`
- 将十六进制解码为 ASCII 即可得到 Flag。

### 4. 获取 Flag
- 最终恢复明文：

```text
putcCTF{try_br3ak1ng_0ut}
```

## 攻击链/解题流程总结

```text
读取 RSA 参数与提示 → 构造 m^e = c + k*n（k 较小）→ 搜索完美六次幂 → 十六进制转 ASCII → Flag
```

## 漏洞分析 / 机制分析

### 根因
- 使用小指数（`e=6`）且明文构造使 `m^e` 与 `n` 的差值很小，导致可通过小范围 `k` 搜索恢复明文。
- 缺少安全填充（如 OAEP）时，RSA 结构性信息会直接暴露在幂关系中。

### 影响
- 攻击者无需分解 `n`，仅依赖整数幂关系与小范围枚举即可恢复明文。
- 当提示或上下文暗示“略大于 n”时，攻击成本显著下降。

### 修复建议（适用于漏洞类题目）
- 使用 RSA-OAEP 等随机填充方案，避免可预测的幂关系。
- 采用标准参数组合（例如 `e=65537` + 正确填充），禁止直接对结构化原文做裸 RSA。
- 对消息编码进行随机化与长度规范化，避免泄露可利用数学结构。

## 知识点
- 低指数 RSA 场景下的 `c + k*n` 提升思路
- 完美幂检测与整数 n 次根
- 裸 RSA 与填充 RSA 的安全差异

## 使用的工具
- Security Hub MCP — `crypto_rsa_low_exponent` 求解低指数提升问题
- Go `math/big` — 本地复现大整数与完美幂检测

## 脚本归档
- Go：[`putcCTF_Exercise.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/putcCTF_Exercise.go){target="_blank"}
- Python：待补（预计文件名：`putcCTF_Exercise.py`）
- 说明：解题代码需包含详细注释

## 命令行提取关键数据（无 GUI）

```bash
# 运行本地 Go 脚本复现求解
go run CTF_Writeups/scripts_go/putcCTF_Exercise.go
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Security Hub MCP | 参数求解 | 秒级 | 直接支持低指数攻击模型，验证快 | 依赖 MCP 环境 |
| Go `math/big` | 本地复现 | 分钟级 | 可离线、可控、便于归档 | 需手写整数根/判幂逻辑 |
| Python `gmpy2` | 快速验证 | 分钟级 | 原型开发快 | 需要额外依赖 |

### 推荐流程

**推荐流程**：先用 MCP 快速命中参数区间 → 再用本地脚本复现并归档结果 → 校验输出格式与 Flag。 

### 工具 A（推荐首选）
- **安装**：配置并启用 `security-hub` MCP
- **详细步骤**：
  1. 输入 `n`、`c`、`e=6`
  2. 调用 `crypto_rsa_low_exponent` 并逐步增大 `max_k`
  3. 提取 `plaintext_hex` 并解码为 ASCII
- **优势**：搜索与验证一体化，适合此类“m^e 略大于 n”题型

### 工具 B（可选）
- **安装**：Go 1.20+
- **详细步骤**：
  1. 读取 `exercise.txt` 参数
  2. 枚举 `k`，检测 `c+k*n` 是否为六次幂
  3. 将根值转字节并打印
- **优势**：可复现、可审计、便于长期沉淀脚本