# Hack For A Change 2026 March - Patient Zero Writeup

## 题目信息

- **比赛**: Hack For A Change 2026 March (UN SDG3)
- **题目**: Patient Zero
- **类别**: Crypto
- **难度**: 中等
- **附件**: `encrypt.py`
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Patient_Zero/encrypt.py){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Patient_Zero){target="_blank"}
- **Flag格式**: `SDG{...}`
- **状态**: 已解

## Flag

```text
SDG{3c00bad87b9ba46afa47052e187cec59}
```

## 解题过程

### 1. 分析加密脚本

`encrypt.py` 实现了一个带固定填充的 RSA 加密：

```python
prefix = b"SDGCTF_SECURE_MSG_V1::"
suffix = b"::END"
padded = prefix + flag + suffix      # 22 + 37 + 5 = 64 bytes
m = bytes_to_long(padded)
c = pow(m, e, n)                     # e = 3
```

公钥参数与密文：

| 参数 | 值 |
|------|-----|
| $n$ | 1024 bits RSA 模数 |
| $e$ | **3**（极小公钥指数） |
| $c$ | 密文 |
| flag 长度 | 37 bytes (296 bits) |

**关键观察**：$e = 3$ 且明文结构大量已知（prefix 22 字节 + suffix 5 字节），仅 flag 的 37 字节未知。

### 2. 确认攻击条件 — Coppersmith 定理

将明文表示为关于 flag 的函数：

$$m = \underbrace{P \cdot 256^{42}}_{\text{prefix 左移}} + \underbrace{x \cdot 256^{5}}_{\text{flag 左移}} + \underbrace{S}_{\text{suffix}}$$

其中 $P$、$S$ 是 prefix / suffix 的整数值，$x$ 是未知的 flag（37 字节 = 296 bits）。

**Coppersmith 定理**：对首一多项式 $f(x) \equiv 0 \pmod{n}$（$\deg f = d$），若存在根 $|x_0| < n^{1/d}$，则可在多项式时间内找到 $x_0$。

验证条件：

$$|x| < 2^{296} \quad\text{vs}\quad n^{1/3} \approx 2^{341}$$

$$2^{296} < 2^{341} \quad\checkmark \quad (\text{余量 45 bits})$$

### 3. 构造多项式并求解

构造关于 $x$ 的多项式：

$$f(x) = (A + B \cdot x)^3 - c \equiv 0 \pmod{n}$$

其中 $A = P \cdot 256^{42} + S$，$B = 256^5$。

将 $f(x)$ 转化为首一多项式后，使用 SageMath 的 `small_roots()` 方法（内部实现了 Coppersmith 的格基约化算法）：

```python
ZmodN = Zmod(n)
PR = PolynomialRing(ZmodN, 'x')
x = PR.gen()
f = (A + B*x)^3 - c
f_monic = f * f.leading_coefficient()^(-1)
roots = f_monic.small_roots(X=2^296, beta=1.0, epsilon=0.02)
```

### 4. 获取 Flag

`small_roots()` 在数秒内返回唯一根：

```text
x = 41410472545770785675586758963835211975745880785476790409379578628170981910321915804072317
```

将 $x$ 转为 37 字节：

```text
SDG{3c00bad87b9ba46afa47052e187cec59}
```

代入原始加密验证 $\text{pow}(m, 3, n) == c$：通过。

## 攻击链/解题流程总结

```text
分析 encrypt.py → 识别 e=3 + 已知填充 → 验证 Coppersmith 条件 (2^296 < n^{1/3}) → 构造首一多项式 → SageMath small_roots() → Flag
```

## 漏洞分析

### 根因

- **公钥指数 $e = 3$ 过小**：使得密文多项式的次数仅为 3，Coppersmith 小根攻击的条件更容易满足
- **确定性填充 (Textbook RSA)**：prefix 和 suffix 完全已知且固定，攻击者只需恢复 37 字节的未知部分
- **无随机化**：没有使用 OAEP 等概率填充方案，明文结构完全可预测

### 影响

攻击者无需分解 $n$，仅凭公钥和密文即可在数秒内恢复明文。

### 修复建议

- 使用标准填充方案（**OAEP**），引入随机性打破明文的可预测结构
- 使用 $e = 65537$ 等较大的公钥指数
- 避免在明文中包含大量已知/固定内容

## 知识点

- **Coppersmith 小根攻击** — 当多项式模 $n$ 存在足够小的根时，可通过格基约化在多项式时间内恢复
- **RSA 小指数攻击** — $e$ 很小时（尤其 $e=3$），配合已知明文结构可直接攻击
- **格基约化 (LLL)** — Coppersmith 方法的核心，将模多项式根的问题转化为短向量问题
- **Howgrave-Graham 定理** — 当格约化后的多项式系数足够小时，模根即为整数根
- **Stereotyped Message Attack** — 已知明文的大部分内容时，恢复未知部分的攻击

??? note "Coppersmith 攻击条件详解"
    **定理 (Coppersmith, 1996)**：设 $f(x)$ 是 $\mathbb{Z}_n[x]$ 上的首一多项式，次数为 $d$。
    若存在 $|x_0| < n^{1/d}$ 使得 $f(x_0) \equiv 0 \pmod{n}$，则可在 $O(\log^6 n)$ 时间内找到 $x_0$。

    **本题参数**：

    - $d = 3$（因为 $e = 3$）
    - 未知量大小：$2^{296}$
    - 上界：$n^{1/3} \approx 2^{341}$
    - 余量：$341 - 296 = 45$ bits

    余量越大，所需的格维度越小，求解越快。SageMath 的 `epsilon` 参数控制精度/速度权衡：
    `epsilon=0.02` 对应约 50 维格，对本题绰绰有余。

## 使用的工具

- **SageMath** — `small_roots()` 内置 Coppersmith 算法实现
- **Docker** — `docker run sagemath/sagemath` 快速获取 SageMath 环境
- **Go `math/big`** — 大整数运算与加密验证

## 脚本归档

- Go：[`HackForAChange2026March_UN_SDG3_Patient_Zero.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/HackForAChange2026March_UN_SDG3_Patient_Zero.go){target="_blank"}
- Python：[`HackForAChange2026March_UN_SDG3_Patient_Zero.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/HackForAChange2026March_UN_SDG3_Patient_Zero.py){target="_blank"}
- 说明：Python 脚本包含 SageMath 求解代码和纯 Python 验证代码；Go 脚本提供参数分析和 Docker 调用求解

## 命令行提取关键数据（无 GUI）

```bash
# 通过 Docker SageMath 一键求解
docker run --rm -i sagemath/sagemath:latest bash -c \
  'cat > /tmp/s.sage && sage /tmp/s.sage' << 'EOF'
n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
e = 3
c = 90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158
prefix = b'SDGCTF_SECURE_MSG_V1::'
suffix = b'::END'
flag_len = 37
P = int.from_bytes(prefix, 'big')
S = int.from_bytes(suffix, 'big')
B = 256^len(suffix)
A = P * 256^(flag_len + len(suffix)) + S
ZmodN = Zmod(n)
PR = PolynomialRing(ZmodN, 'x')
x = PR.gen()
f = (A + B*x)^3 - c
f_monic = f * f.leading_coefficient()^(-1)
roots = f_monic.small_roots(X=2^(flag_len*8), beta=1.0, epsilon=0.02)
for r in roots:
    ri = int(r)
    m = A + B * ri
    if pow(m, 3, n) == c:
        print(ri.to_bytes(flag_len, 'big').decode())
EOF
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Crypto 工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **SageMath Jupyter** | 格基约化 + 求根 | ~1 分钟 | 交互式调试，可视化输出 | 需要 Docker |
| **SageMath CLI** | 格基约化 + 求根 | ~5 秒 | `small_roots()` 一行解决 | 需要安装/Docker |
| **RsaCtfTool** | RSA 自动攻击 | 不直接适用 | 自动识别多种 RSA 漏洞 | 不支持自定义 padding |
| **Go math/big** | 验证 + 分析 | 即时 | 编译快、无依赖 | 无格基约化库 |

### 推荐流程

**推荐流程**：分析 encrypt.py 识别 e=3 → SageMath `small_roots()` 求解 → 验证 flag。

### SageMath Jupyter（推荐首选）

通过 Docker 启动 SageMath Jupyter Notebook，在浏览器中交互式求解。

**启动环境**：
```bash
# 启动 SageMath Jupyter（端口映射到 8888）
docker run -d --name sagemath -p 8888:8888 \
  sagemath/sagemath:latest \
  sage -n jupyter --no-browser --ip=0.0.0.0 --port=8888

# 查看访问 URL（含 token）
docker logs sagemath 2>&1 | grep token
# 输出示例: http://127.0.0.1:8888/tree?token=3f9682...
```

浏览器打开日志中的 URL，点击 **New → SageMath 10.8** 新建 Notebook，输入以下代码并 `Shift+Enter` 运行：

```python
# Cell 1: Patient Zero - RSA e=3 Coppersmith Attack
n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
e = 3
c = 90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158
prefix = b'SDGCTF_SECURE_MSG_V1::'
suffix = b'::END'
flag_len = 37

P = int.from_bytes(prefix, 'big')
S = int.from_bytes(suffix, 'big')
B = 256^len(suffix)
A = P * 256^(flag_len + len(suffix)) + S

ZmodN = Zmod(n)
PR.<x> = PolynomialRing(ZmodN)
f = (A + B*x)^3 - c
f_monic = f * f.leading_coefficient()^(-1)

# epsilon=0.05 约1分钟出结果; epsilon=0.02 更精确但需5+分钟
roots = f_monic.small_roots(X=2^(flag_len*8), beta=1.0, epsilon=0.05)
print(f'Roots: {roots}')
for r in roots:
    ri = int(r)
    m = A + B * ri
    if pow(m, 3, n) == c:
        flag = ri.to_bytes(flag_len, 'big')
        print(f'Flag: {flag.decode()}')
```

运行输出：

```text
Roots: [41410472545770785675586758963835211975745880785476790409379578628170981910321915804072317]
Flag: SDG{3c00bad87b9ba46afa47052e187cec59}
```

**`epsilon` 参数对比**：

| epsilon | 格维度 | Docker 内耗时 | 说明 |
|---------|--------|--------------|------|
| 0.02 | ~50 | 5+ 分钟 | 精确，适合 CLI 批量跑 |
| 0.05 | ~20 | ~1 分钟 | 推荐，速度与成功率兼顾 |
| 0.10 | ~10 | ~10 秒 | 本题余量 45 bits 刚好卡边界，可能找不到 |

**优势**：交互式环境，可逐步调试多项式构造、观察中间结果，适合学习和探索。

---

### SageMath CLI（快速求解）

- **安装**：
```bash
# Docker 方式（推荐，无需本地安装）
docker pull sagemath/sagemath

# 或 conda 安装
conda install -c conda-forge sage
```
- **详细步骤**：
  1. 从 `encrypt.py` 提取 prefix、suffix、flag_len
  2. 构造多项式 `f(x) = (A + B*x)^3 - c`，转为首一形式
  3. 调用 `f_monic.small_roots(X=2^296, beta=1.0, epsilon=0.02)`
  4. 将返回的根转为字节即得 flag
- **优势**：内置 Coppersmith/LLL 实现，一行代码完成核心攻击

---

### RsaCtfTool（可选）

- **安装**：
```bash
git clone https://github.com/RsaCtfTool/RsaCtfTool.git
cd RsaCtfTool && pip install -r requirements.txt
```
- **详细步骤**：本题使用自定义 padding，RsaCtfTool 的内置攻击不直接适用，但可参考其 `small_e` 模块的实现思路
- **优势**：对标准 RSA 题目（无自定义 padding）可一键破解
