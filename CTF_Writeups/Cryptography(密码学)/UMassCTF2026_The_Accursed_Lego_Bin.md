# UMassCTF 2026 - The Accursed Lego Bin Writeup

## 题目信息
- **比赛**: UMassCTF 2026
- **题目**: The Accursed Lego Bin
- **类别**: Crypto
- **难度**: 简单
- **附件/URL**: `encoder.py`、`output.txt`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/The%20Accursed%20Lego%20Bin/output.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/The%20Accursed%20Lego%20Bin){target="_blank"}
- **Flag格式**: `UMASS{...}`
- **状态**: 已解

## Flag

```text
UMASS{tH4Nk5_f0R_uN5CR4m8L1nG_mY_M3554g3}
```

## 解题过程

### 1. 初始侦察 / 文件识别
- 入口点是附件 `encoder.py` 和 `output.txt`。
- `encoder.py` 的核心逻辑并不复杂：
  - 先把固定明文 `I_LOVE_RNG` 做一次 RSA 加密，得到 `(n, seed)`。
  - 再把 flag 转成 bit 数组。
  - 用 `random.seed(seed * (i + 1))` 连续执行 10 次 `random.shuffle(flag_bits)`。
  - 最后把被打乱的 bit 数组转成十六进制字符串输出到 `output.txt`。
- 这意味着真正要解决的问题有两个：
  1. 从 `output.txt` 里的 `seed` 恢复出洗牌用的随机种子。
  2. 按相反顺序撤销 10 次 `shuffle`，把 bit 数组还原。

### 2. 关键突破点一
- 题目把 RSA 写得很像“加密后不可逆”，但这里其实是裸 RSA，而且消息非常小：

```python
text = "I_LOVE_RNG"
e = 7
```

- `I_LOVE_RNG` 只有 10 字节，也就是 79 bit 左右。
- 第一次 RSA 使用的是 2048 bit 的素数 `p`、`q`，所以模数 `n` 大约是 4096 bit。
- 由于明文极小，有：

$$
m^7 < n
$$

- 因此第一次“RSA 加密”实际上没有发生模回绕：

$$
seed = m^7
$$

- 接着脚本又计算：

$$
enc\_seed = seed^7 \bmod n
$$

- 但这里同样不会回绕，因为：

$$
seed^7 = (m^7)^7 = m^{49} < n
$$

- 所以 `output.txt` 里的 `seed` 实际上满足：

$$
enc\_seed = seed^7
$$

- 这就变成了一个普通的大整数七次根问题。直接对 `enc_seed` 开整数 7 次根，就能精确恢复出用于洗牌的 `seed`。

### 3. 关键突破点二
- 还原出 `seed` 后，就能完全复现题目中的伪随机序列：

```python
for i in range(10):
    random.seed(seed * (i + 1))
    random.shuffle(flag_bits)
```

- 难点只在于 `random.shuffle` 是原地置换，不能简单再 `shuffle` 一次“洗回去”。
- 正确做法是：
  - 对每一轮重新生成同样的置换下标。
  - 从最后一轮开始逆序处理，即 `i = 9 -> 0`。
  - 根据该轮置换构造逆映射，把当前位置的 bit 放回打乱前的位置。
- 全部 10 轮逆完之后，再每 8 bit 重新拼成字节并按 ASCII 解码，即可得到明文 flag。

### 4. 获取 Flag
- 还原后的结果为：

```text
UMASS{tH4Nk5_f0R_uN5CR4m8L1nG_mY_M3554g3}
```

## 攻击链 / 解题流程总结

```text
阅读 encoder.py -> 发现是固定短明文 + e=7 的裸 RSA -> 由于 m^7 和 m^49 都小于 n，可直接对输出 seed 开整数七次根 -> 复现 10 次 random.seed/shuffle -> 逆置换恢复 bit 数组 -> 转回 ASCII 得到 Flag
```

## 漏洞分析 / 机制分析

### 根因
- 使用了裸 RSA，没有任何填充。
- 明文 `I_LOVE_RNG` 太短，指数 `e = 7` 也较小，导致幂结果始终小于模数，整个“加密”退化成普通整数幂。
- 后续所谓“保护 flag”的方法只是按可复现的伪随机置换打乱 bit 顺序，并不具备真正的密码学安全性。

### 影响
- 攻击者不需要分解 `n`，甚至不需要碰到 RSA 的困难部分，只要开整数根就能恢复洗牌种子。
- 一旦种子泄露，10 轮 `shuffle` 全都可以被逐轮撤销，最终完整恢复 flag。

### 修复建议（适用于漏洞类题目）
- 不要使用裸 RSA，必须使用标准填充方案，如 RSA-OAEP。
- 不要把“随机打乱顺序”当作加密手段，尤其不要用可预测、可重现的 PRNG 种子。
- 如果只是想保护消息，应直接使用标准对称加密方案，例如 AES-GCM 之类的认证加密。

## 知识点
- 裸 RSA 在小明文、小指数场景下的整数幂泄露问题
- 整数 n 次根恢复
- `random.shuffle` 的逆置换构造
- bit 级置乱并不等于安全加密

## 使用的工具
- Python 3：本地编写和运行复现脚本
- `encoder.py`：直接提供了题目的完整加密流程

## 脚本归档
- Go：[`UMassCTF2026_The_Accursed_Lego_Bin.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/UMassCTF2026_The_Accursed_Lego_Bin.go){target="_blank"}
- Python：[`UMassCTF2026_The_Accursed_Lego_Bin.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/UMassCTF2026_The_Accursed_Lego_Bin.py){target="_blank"}
- 说明：Go 版复刻了 CPython `random.seed` / `getrandbits` / `shuffle` 的关键行为；两个脚本都会读取归档后的 `output.txt` 并自动恢复 flag

## 命令行提取关键数据（无 GUI）

```bash
go run CTF_Writeups/scripts_go/UMassCTF2026_The_Accursed_Lego_Bin.go

python CTF_Writeups/scripts_python/UMassCTF2026_The_Accursed_Lego_Bin.py
```

## 推荐工具与优化解题流程

> 这题核心不在“高级密码分析”，而在识别实现层面的错误安全假设。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| 阅读源码 | 初筛 | 分钟级 | 直接定位逻辑漏洞 | 依赖对代码语义敏感 |
| Python 本地脚本 | 复现求解 | 秒级 | 逆置换与大整数处理都很方便 | 需要自己实现逆映射 |
| Sage / `math.isqrt` 风格工具 | 数学验证 | 秒级 | 适合验证整数根关系 | 本题没有必要额外引入 |

### 推荐流程

**推荐流程**：先看源码确认是否存在裸 RSA 或伪随机误用 -> 用本地脚本开整数根恢复种子 -> 逆置换恢复 bit 数组 -> 输出 Flag。

### 工具 A（推荐首选）
- **安装**: Python 3
- **详细步骤**:
  1. 读取 `output.txt` 中的 `seed` 和 `flag`
  2. 对 `seed` 做整数 7 次根，恢复真实洗牌种子
  3. 倒序逆转 10 次 `random.shuffle`
  4. 将 bit 数组重新编码成字符串
- **优势**: 足够直接，可完全复现题目逻辑

### 工具 B（可选）
- **安装**: SageMath 或其他支持大整数的数学环境
- **详细步骤**:
  1. 验证 `m^7 < n` 与 `m^49 < n`
  2. 对 `enc_seed` 做整数根验证
  3. 再回到 Python 或其他脚本环境处理逆置换
- **优势**: 适合做数学关系校验
