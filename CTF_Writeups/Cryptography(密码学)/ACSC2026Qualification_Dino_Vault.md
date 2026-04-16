# ACSC Qualification 2026 - Dino Vault Writeup

!!! warning "发布提醒"
    官方 Qualification 页面显示本轮时间为 **2026-03-01 18:00 CEST ～ 2026-05-01 18:00 CEST**。当前文档适合作为**本地归档草稿**；若比赛尚未结束，请勿提前公开发布。

## 题目信息
- **比赛**: ACSC Qualification 2026（Austria Cyber Security Challenge 2026 Qualification）
- **题目**: Dino Vault
- **类别**: Crypto
- **难度**: 中等
- **附件/URL**: `app.py` · `Dockerfile` · `nc port.dyn.acsc.land 30853` · [平台](https://ctf.acsc.land/){target="_blank"}
- **附件链接**: [下载 app.py](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/dino-vault/app.py){download} · [下载 Dockerfile](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/dino-vault/Dockerfile){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/dino-vault){target="_blank"}
- **Flag格式**: `dach2026{...}`
- **状态**: 已解

## Flag

```text
dach2026{R5A_a_d1n0s5r_0f_1ts_0wn_2fqkncq16x3mbtkf}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点可以直接用 `nc port.dyn.acsc.land 30853` 交互，也可以先读附件 `app.py`
- 服务支持三类关键操作：
  1. 创建自己的恐龙
  2. 查看已有恐龙
  3. 下载某只恐龙的加密 DNA
- 内置列表里最值得关注的是：

```text
- Vexillum Rex
- Pedosaurus
- Despotiraptor
- Planosaurus
```

- 其中 `Vexillum Rex` 的构造里直接把 flag 写进了原始描述字符串：

```python
Dino(
    name="Vexillum Rex",
    dna=Dino.to_dna(f"Has a crown and {FLAG} written on its back"),
    vault_key=getPrime(primesize),
)
```

### 2. 从哪里看出来是 RSA 加密
- 题目名字和界面没有直接写 “RSA”，但 `app.py` 里有非常明显的 textbook RSA 特征：

```python
transmission_key = getPrime(primesize)
dinosaur_modulation_index = transmission_key * sel2f.vault_key
evergreen_number = 2**16 + 1
resampled_dna = pow(bytes_to_long(self.dna.encode()), evergreen_number, dinosaur_modulation_index)
encrypted_dna = long_to_bytes(resampled_dna).hex()
```

!!! note "关于附件中的 `sel2f`"
    发布的 `app.py` 在这一行里写成了 `sel2f.vault_key`，这是一个明显笔误。远程服务能够正常返回下载结果，说明实际运行逻辑等价于 `self.vault_key`。  
    不过这不影响我们识别它的密码学结构：**两个大素数相乘得到模数，再做 `pow(m, 65537, n)`，本质上依然是裸 RSA**。

可以从这几处判断：

1. **模数是两个大素数的乘积**
   - `transmission_key = getPrime(primesize)`
   - `self.vault_key` 也是 `getPrime(primesize)` 生成的素数
   - 然后 `n = transmission_key * self.vault_key`

2. **指数是 65537**
   - `2**16 + 1 = 65537`
   - 这是 RSA 最常见的公开指数 `e`

3. **加密公式是 `pow(m, e, n)`**
   - `pow(bytes_to_long(...), evergreen_number, dinosaur_modulation_index)`
   - 也就是标准的

$$
c = m^e \bmod n
$$

4. **明文先转整数，密文再转回字节**
   - `bytes_to_long(...)`
   - `long_to_bytes(...)`
   - 这也是 RSA 题里非常典型的处理方式

所以，虽然题目文本没有说，但从代码结构上可以非常明确地判断：**这就是裸 RSA**。

### 3. 关键突破点一：先理解 DNA 编码
- `Dino.to_dna()` 会把每个字符拆成 4 组 2-bit，再映射到 `A/T/G/C`

```python
lookup = ["A", "T", "G", "C"]
```

- 映射关系其实就是：

```text
A -> 0
T -> 1
G -> 2
C -> 3
```

- 例如自己创建一只恐龙，信息填 `A`，那么：
  - `ord('A') = 65 = 0b01000001`
  - 按低位到高位每 2 bit 切分：`01 00 00 01`
  - 对应 DNA：`TAAT`

- 这一步很有用，因为它能验证“RSA 解密出来的并不是原始英文，而是 DNA 串；还需要再逆一次编码”

### 4. 关键突破点二：同一只恐龙重复下载两次
- 真正的漏洞在于 **每只恐龙的 `vault_key` 是固定的**，但每次下载都会新生成一个 `transmission_key`

```python
transmission_key = getPrime(primesize)
dinosaur_modulation_index = transmission_key * self.vault_key
```

- 对于同一只恐龙（例如 `Vexillum Rex`），在**同一连接/session**里连续下载两次：

$$
n_1 = p \cdot q_1
$$

$$
n_2 = p \cdot q_2
$$

其中：
- `p = vault_key`（同一只恐龙固定不变）
- `q_1, q_2 = transmission_key`（每次下载重新生成）

- 因此直接有：

$$
\gcd(n_1, n_2) = p
$$

- 这就把 RSA 模数的一个素因子直接算出来了

### 5. 关键突破点三：分解模数并解密
- 拿到 `p = gcd(n1, n2)` 后，就可以：

$$
q = \frac{n_1}{p}
$$

$$
\varphi(n_1) = (p-1)(q-1)
$$

$$
d = e^{-1} \bmod \varphi(n_1)
$$

!!! note "为什么不是直接用 `1/65537`？"
    这里的 `e^{-1}` 不是实数意义下的倒数 `1/e`，而是**模逆元**。  
    我们要求的是一个**整数** `d`，使得：

    $$
    e \cdot d \equiv 1 \pmod{\varphi(n)}
    $$

    例如如果 `e = 3`、`\varphi(n) = 10`，那么 `d = 7`，因为：

    $$
    3 \cdot 7 = 21 \equiv 1 \pmod{10}
    $$

    这和 `1/3 = 0.333...` 完全不是一个概念。  
    RSA 解密指数必须是**模 \(\varphi(n)\)** 的乘法逆元，否则就无法保证：

    $$
    (m^e)^d = m^{ed} \equiv m \pmod n
    $$

    所以即便 `1/65537` 这个实数看起来很小，它在 RSA 里也没有意义；真正有意义的是满足 `e*d ≡ 1 (mod φ(n))` 的那个大整数 `d`。

- 再对其中一组密文做标准 RSA 解密：

$$
m = c_1^d \bmod n_1
$$

- 得到的 `m` 不是英文描述，而是一串 `A/T/G/C` 的 DNA 字符串，再按 4 个字符一组逆回 ASCII

### 6. 获取 Flag
- 对你提供的两组 `Vexillum Rex` 下载结果做 `gcd(n1, n2)` 后，成功恢复共享质因子
- 解密并逆 DNA 编码后得到：

```text
Has a crown and dach2026{R5A_a_d1n0s5r_0f_1ts_0wn_2fqkncq16x3mbtkf} written on its back
```

- 因此 flag 为：

```text
dach2026{R5A_a_d1n0s5r_0f_1ts_0wn_2fqkncq16x3mbtkf}
```

## 攻击链/解题流程总结

```text
阅读 app.py 识别 pow(m, 65537, n) 的裸 RSA 结构 → 发现同一恐龙重复下载会复用 vault_key → 在同一连接里对 Vexillum Rex 下载两次 → gcd(n1, n2) 恢复共享质因子 → 分解 n1 解 RSA → 把 DNA 串逆编码回英文 → 提取 flag
```

## 漏洞分析 / 机制分析

### 根因
- **RSA 模数生成方式错误**：同一只恐龙反复使用固定素因子 `vault_key`
- **同一明文被不同但相关的模数重复加密**
- **使用裸 RSA**：没有 OAEP 等随机填充保护结构
- **flag 所在明文目标可预测**：`Has a crown and ... written on its back`

### 影响
- 对同一只恐龙下载两次即可通过 `gcd(n1, n2)` 恢复共享质因子
- 一旦分解出模数，就能完整解密该恐龙的 DNA
- 由于 `Vexillum Rex` 的描述中直接嵌入 flag，最终可直接泄露 flag

### 修复建议（适用于漏洞类题目）
- 不要让不同 RSA 模数共享任何素因子
- 为每次加密生成独立且完整的新密钥对，而不是只替换一个质因子
- 使用 **RSA-OAEP** 等带随机填充的标准方案，而不是裸 RSA
- 不要把敏感信息直接嵌入结构化、可预测的明文模板

## 知识点
- 如何从代码识别 RSA：`n = p*q`、`e = 65537`、`pow(m, e, n)`
- RSA shared-prime / GCD attack（共享素因子攻击）
- 自定义字母表编码与逆编码（A/T/G/C 还原字符）

??? note "RSA 与模运算扩展阅读"
    如果对 `e^{-1} mod φ(n)`、模运算法则、同余方程求解还不熟，可以看这篇专题：  
    [:material-book-open-variant: RSA 与模运算知识点扩展](rsa_modular_arithmetic.md)

## 使用的工具
- Python 标准库 `math.gcd` — 计算共享质因子
- `Crypto.Util.number` — 求逆、RSA 解密、整数/字节转换
- 本地阅读 `app.py` — 确认 RSA 构造与 DNA 编码方式

## 脚本归档
- Go：[`ACSC2026Qualification_Dino_Vault.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/ACSC2026Qualification_Dino_Vault.go){target="_blank"}
- Python：[`ACSC2026Qualification_Dino_Vault.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/ACSC2026Qualification_Dino_Vault.py){target="_blank"}
- 说明：脚本支持直接输入两组密文/模数对进行离线求解

## 命令行提取关键数据（无 GUI）

```bash
go run CTF_Writeups/scripts_go/ACSC2026Qualification_Dino_Vault.go \
  -ciphertext1 <hex1> -modulus1 <n1> \
  -ciphertext2 <hex2> -modulus2 <n2>

python CTF_Writeups/scripts_python/ACSC2026Qualification_Dino_Vault.py \
  --ciphertext1 <hex1> --modulus1 <n1> \
  --ciphertext2 <hex2> --modulus2 <n2>
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Go 本地脚本 | 完整求解 | 秒级 | 单文件、易归档、无第三方依赖 | 参数较长时命令行不够友好 |
| Python 本地脚本 | 完整求解 | 秒级 | `gcd + RSA + 逆编码` 一体化 | 需要自己解析题目输出 |
| Sage / Python 大整数环境 | 数论验证 | 秒级 | 适合快速验证 `gcd`、求逆与解密 | 归档性不如纯脚本 |
| `nc` | 交互获取数据 | 秒级 | 拿两组下载结果最直接 | 不能自动完成数论求解 |

### 推荐流程

**推荐流程**：先从代码认出 RSA → 在同一连接里对 `Vexillum Rex` 下载两次 → 提取两组 `modulation index` 与密文 → 用脚本做 `gcd` 分解并逆 DNA 编码 → 拿到 flag。 

### 工具 A（推荐首选）
- **安装**：Python 3.10+ 与 `pycryptodome`
- **详细步骤**：
  1. 收集同一连接中的两组 `(ciphertext, modulus)`
  2. 计算 `p = gcd(n1, n2)`
  3. 分解 `n1`，恢复私钥 `d`
  4. 解密并将 DNA 还原为原始英文描述
- **优势**：最贴合题目机制，便于长期归档

### 工具 B（可选）
- **安装**：SageMath 或支持大整数数论的环境
- **详细步骤**：
  1. 用 `gcd(n1, n2)` 找共享质因子
  2. 直接在 REPL 里恢复 `d`
  3. 另写一小段脚本逆 DNA 编码
- **优势**：适合交互式验证每一步数论结论
