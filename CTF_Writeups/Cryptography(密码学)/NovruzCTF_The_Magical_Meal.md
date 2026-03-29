# novruzCTF - The Magic Meal (Crypto)

## 题目信息

- **题目名称**: The Magic Meal（神奇的饭菜）
- **类别**: Crypto
- **难度**: 中等
- **题目描述**:
- 原文:
- There was a team in the CTF world — a team that cracked ciphers in seconds and always stood at the top of the rankings. Rivals would whisper: "Are these people even human? How do they think so fast?" No one knew their secret. The team's cryptographer — the quiet, thoughtful one who solved the most complex ciphers at every competition and tackled the hardest challenges alone — drew his strength from one thing. A small, simple, seemingly ordinary magical meal. What was the meal? Only he knew. One thing must be said clearly — the cryptographer never looked down on other teams. On the contrary, he considered every rival worthy and treated every competition like a real battle. That is why he guarded his secret so carefully — because if it ever got out, the game would become equal. And in an equal game, everything would have to start over. The final competition came to an end. The team won again. The cryptographer, overflowing with joy, hurried out of the hall to celebrate the victory with his friends and teammates — he left in such a rush that a piece of paper remained on the table. On the paper, only numbers were written:

You picked up the paper. You recognized the encryption immediately. Can you find the name of the magical meal?

flag format: novruzCTF{}
- 译文:
在CTF（夺旗赛）的世界里，有一支队伍——他们能在几秒钟内破解密码，始终高居榜首。对手们私下议论纷纷：“这些人真的是人类吗？他们怎么能反应这么快？” 没人知道他们的秘密。这支队伍的密码破译员——一个沉默寡言、心思缜密的人，每次比赛都能破解最复杂的密码，独自应对最棘手的挑战——他的力量源自于一件事。一顿看似普通却充满魔力的饭菜。那是什么？只有他自己知道。必须明确的是，这位密码破译员从不轻视其他队伍。相反，他认为每个对手都值得尊敬，把每场比赛都当作真正的战斗。正因如此，他才如此小心翼翼地守护着自己的秘密——因为一旦泄露，比赛就会变得势均力敌。而一旦势均力敌，一切都将重头再来。最终的比赛结束了。这支队伍再次赢得了胜利。密码破译员欣喜若狂，急忙跑出大厅去和朋友队友们庆祝胜利——他走得太匆忙，以至于桌上还留着一张纸。纸上只写着一些数字：

你捡起了那张纸。你立刻认出了上面的加密信息。你能找到这道神奇菜肴的名字吗？

flag格式：novruzCTF{}
- CTF 密码破译员留下了一张纸，上面写着 ElGamal 加密参数。找到加密的"神奇菜肴"名称。
- **状态**: 已解

## Flag

```text
novruzCTF{R3db0X_r3suL_s3k3rbura_x0slay1r}
```

## 解题过程

### 1. 识别密码体制

图片中的纸条包含参数 `p, g, h, c1, c2`，这是经典的 **ElGamal 加密** 结构：

| 参数 | 含义 |
|------|------|
| $p$ | 大素数（模数） |
| $g$ | 生成元 |
| $h = g^x \mod p$ | 公钥 |
| $c_1 = g^k \mod p$ | 密文第一部分 |
| $c_2 = m \cdot h^k \mod p$ | 密文第二部分 |

从图片读取的参数：

```text
p  = 1905671816403772611477075447515791022372594380344434356222414517909417652709503859707116441682578631751
g  = 35184372088891
h  = 516040377462955752574346949927976425016812503608111809810810609404241010158862043385306853745074259882
c1 = 1325105302324133202030863283172149567672069489633456911926998051053347443881714632147496615921683435710
c2 = 1105652739004198834387911095412299689766266872864244844677769021917226737321429032589227873083116104228
```

$p$ 为 103 位十进制数（340 bits）。

### 2. 寻找漏洞 — $p-1$ 光滑

ElGamal 的安全性依赖于离散对数问题（DLP）的困难性。如果 $p-1$ 是**光滑数**（只有小素因子），可以使用 **Pohlig-Hellman 算法**将 DLP 分解为多个小子群上的 DLP。

对 $p-1$ 进行因式分解（仅耗时 112ms）：

$$p-1 = 2 \times 3 \times 5^3 \times 7^3 \times 11^3 \times 13 \times 17^2 \times 19^3 \times 23^2 \times 29^3 \times 31^3 \times 37^2 \times 41^3 \times 43^3 \times 47 \times 53^2 \times 59^3 \times 61^3 \times 67^2 \times 71^3 \times 73^2 \times 83^3 \times 89^3 \times 97^3 \times 3863959211057779$$

**最大素因子仅 52 bits**，$p-1$ 极其光滑！这使得 Pohlig-Hellman 攻击完全可行。

### 3. Pohlig-Hellman 攻击

**算法步骤：**

对 $p-1$ 的每个素幂因子 $q^e$：
1. 计算子群生成元 $g' = g^{(p-1)/q^e} \mod p$
2. 计算子群中的目标 $h' = h^{(p-1)/q^e} \mod p$
3. 用 **Baby-Step Giant-Step (BSGS)** 在阶为 $q$ 的子群中求离散对数
4. 对高次幂 $q^e$，逐位提取每一位

最后用**中国剩余定理 (CRT)** 合并所有子群的结果，得到完整私钥。

```text
x = 952835908201886305738537723757895511186297190172217178111207258954708826354751929853558221155448581233
```

验证：$g^x \mod p = h$ ✓

### 4. ElGamal 解密

$$s = c_1^x \mod p$$

$$m = c_2 \times s^{-1} \mod p$$

解密得到：

```text
m = 60387477779554669378114590672242601795096187453427467994077246676480734538398689428621878717523784317
```

转换为字节：

```text
hex: 6e6f7672757a4354467b5233646230585f723373754c5f73336b3372627572615f7830736c617931727d
text: novruzCTF{R3db0X_r3suL_s3k3rbura_x0slay1r}
```

## 漏洞分析

### 根因

$p-1$ 是光滑数 — 所有素因子都很小（最大仅 52 bits）。这使得 340 bits 的素数 $p$ 提供的安全性远低于预期。

### 安全建议

生成 ElGamal 参数时应使用**安全素数** $p = 2q + 1$（其中 $q$ 也是素数），确保 $p-1$ 不光滑。

## 知识点

- **ElGamal 加密体制** — 基于离散对数问题的公钥加密
- **Pohlig-Hellman 攻击** — 当群阶光滑时，将大 DLP 分解为小 DLP
- **Baby-Step Giant-Step (BSGS)** — $O(\sqrt{n})$ 求解小子群离散对数
- **中国剩余定理 (CRT)** — 合并模不同素幂的同余方程
- **光滑数 (Smooth Number)** — 所有素因子不超过某个上界的整数

## 解题代码

使用 Go 语言实现，见 `solve_elgamal.go`，主要组件：

| 函数 | 功能 |
|------|------|
| `factorize()` | 试除法 + Pollard's rho 分解 $p-1$ |
| `babyStepGiantStep()` | BSGS 求子群离散对数 |
| `pohligHellman()` | Pohlig-Hellman 分治求解 |
| `crt()` | 中国剩余定理合并 |

总耗时约 3 分钟（最大因子 52 bits 的 BSGS 是性能瓶颈）。

**Go 版本解题脚本（可复现）**：
```bash
# 位于项目根目录

go run solve_elgamal.go
```

## 使用的工具

- Go `math/big` — 大整数运算

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_The_Magical_Meal.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_The_Magical_Meal.py`

## 命令行提取关键数据（无 GUI）

```bash
# 将题目参数保存为 Sage 脚本（便于复现实验）
cat > params.sage <<'EOF'
p  = 1905671816403772611477075447515791022372594380344434356222414517909417652709503859707116441682578631751
g  = 35184372088891
h  = 516040377462955752574346949927976425016812503608111809810810609404241010158862043385306853745074259882
c1 = 1325105302324133202030863283172149567672069489633456911926998051053347443881714632147496615921683435710
c2 = 1105652739004198834387911095412299689766266872864244844677769021917226737321429032589227873083116104228
print(factor(p-1))
EOF

sage params.sage
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Crypto 工具推荐。

### 1. SageMath — 数学计算首选（推荐）

[SageMath](https://www.sagemath.org/) 是开源的数学计算框架，内置离散对数求解器，可直接破解本题。

**安装：**
```bash
# Docker 方式（推荐）
docker run -it sagemath/sagemath

# 或 conda 安装
conda install -c conda-forge sage
```

**详细操作步骤：**

**Step 1：定义参数**
```python
sage: p = 1905671816403772611477075447515791022372594380344434356222414517909417652709503859707116441682578631751
sage: g = 35184372088891
sage: h = 516040377462955752574346949927976425016812503608111809810810609404241010158862043385306853745074259882
sage: c1 = 1325105302324133202030863283172149567672069489633456911926998051053347443881714632147496615921683435710
sage: c2 = 1105652739004198834387911095412299689766266872864244844677769021917226737321429032589227873083116104228
```

**Step 2：检查 $p-1$ 是否光滑**
```python
sage: factor(p - 1)
# 输出所有素因子，确认最大因子很小 → p-1 光滑
```

**Step 3：直接求离散对数**
```python
sage: F = GF(p)          # 创建有限域
sage: x = discrete_log(F(h), F(g))  # Sage 自动选择最优算法（Pohlig-Hellman）
sage: print(f"私钥 x = {x}")
```

**Step 4：ElGamal 解密**
```python
sage: s = power_mod(int(c1), int(x), int(p))
sage: s_inv = inverse_mod(int(s), int(p))
sage: m = (int(c2) * s_inv) % int(p)
sage: bytes.fromhex(hex(m)[2:])
# 输出: b'novruzCTF{R3db0X_r3suL_s3k3rbura_x0slay1r}'
```

**优势**：`discrete_log()` 一条命令自动完成 Pohlig-Hellman + CRT，无需手写算法。

---

### 2. RsaCtfTool — RSA/ElGamal 攻击工具箱

[RsaCtfTool](https://github.com/RsaCtfTool/RsaCtfTool) 主要针对 RSA，但其设计思路可以参考。对 ElGamal 需要手写脚本，但工具内置的大数运算库可以辅助。

**安装：**
```bash
git clone https://github.com/RsaCtfTool/RsaCtfTool.git
cd RsaCtfTool && pip install -r requirements.txt
```

**适用场景**：如果题目是 RSA 而非 ElGamal，可直接使用：
```bash
python RsaCtfTool.py -n <modulus> -e <exponent> --uncipher <ciphertext>
# 自动尝试多种攻击：Wiener、Fermat、Pollard p-1 等
```

---

### 3. CyberChef — 编码转换辅助

[CyberChef](https://gchq.github.io/CyberChef/) 在线工具，适合快速完成最后的数字→字节→文本转换。

**详细操作步骤：**

**Step 1：大整数转 Hex**
- 使用 "From Decimal" 模块将解密后的 $m$ 值转为 hex

**Step 2：Hex 转文本**
- 使用 "From Hex" 模块将 hex 转为可读文本
- 直接看到 flag

**配方链接示例**：
```text
From_Decimal → To_Hex → From_Hex
```

**优势**：无需编程，拖拽操作完成编码转换。

---

### 4. 自研 Crypto 工具包（ctf_tools/crypto）

项目中已有的密码学工具包也可以辅助本题：

```bash
cd ctf_tools/crypto

# 哈希验证
./crypto_toolkit hash -a sha256 -t "novruzCTF{R3db0X_r3suL_s3k3rbura_x0slay1r}"

# 编码转换
./crypto_toolkit decode -e hex -t "6e6f7672757a435446..."
```

---

### 工具对比总结

| 工具 | 适用场景 | 本题耗时 | 优点 |
|------|---------|---------|------|
| **SageMath** | 离散对数、数论计算 | ~2 分钟 | `discrete_log()` 一行解决，内置 Pohlig-Hellman |
| **CyberChef** | 编码转换 | ~30 秒 | 在线可视化操作 |
| **RsaCtfTool** | RSA 攻击 | 不直接适用 | RSA 题一键破解 |
| **Go math/big** | 手写算法 | ~3 分钟 | 学习价值高，但代码量大 |

**推荐流程**：SageMath `factor(p-1)` 确认光滑 → `discrete_log()` 求私钥 → 解密 → CyberChef 转文本。
