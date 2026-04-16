# RSA 与模运算知识点扩展

> 本文档是 [Dino Vault Writeup](ACSC2026Qualification_Dino_Vault.md) 的补充知识点，重点解释 RSA 中常见的模运算规则、模逆元、同余方程求解，以及为什么 `d = e^{-1} mod φ(n)` 不是普通倒数。

---

## 1. 模运算与同余的基本概念

### 1.1 什么是 `a mod m`

`a mod m` 表示 `a` 除以 `m` 后的余数。通常取：

```text
0 <= a mod m < m
```

例如：

```text
17 mod 5 = 2
23 mod 7 = 2
-1 mod 7 = 6
```

在 Python / Go 的大整数场景里，最终通常希望把余数规范到 `[0, m-1]`。

### 1.2 什么是同余

如果 `a` 和 `b` 除以 `m` 的余数相同，就说：

$$
a \equiv b \pmod m
$$

等价定义是：

$$
m \mid (a-b)
$$

也就是 `a-b` 能被 `m` 整除。

例子：

```text
17 ≡ 2 (mod 5)
23 ≡ 2 (mod 7)
100 ≡ 28 (mod 12)
```

因为：

```text
17 - 2 = 15 = 5 * 3
23 - 2 = 21 = 7 * 3
100 - 28 = 72 = 12 * 6
```

---

## 2. 模运算的常用运算法则

如果：

$$
a \equiv b \pmod m,\quad c \equiv d \pmod m
$$

那么下面这些运算都成立。

### 2.1 加法

$$
a+c \equiv b+d \pmod m
$$

等价地：

$$
(a+c)\bmod m = ((a\bmod m)+(c\bmod m))\bmod m
$$

例子：

```text
17 ≡ 2 (mod 5)
13 ≡ 3 (mod 5)
17 + 13 = 30 ≡ 0 (mod 5)
2 + 3 = 5 ≡ 0 (mod 5)
```

### 2.2 减法

$$
a-c \equiv b-d \pmod m
$$

例子：

```text
17 ≡ 2 (mod 5)
13 ≡ 3 (mod 5)
17 - 13 = 4 ≡ 4 (mod 5)
2 - 3 = -1 ≡ 4 (mod 5)
```

### 2.3 乘法

$$
a\cdot c \equiv b\cdot d \pmod m
$$

例子：

```text
17 ≡ 2 (mod 5)
13 ≡ 3 (mod 5)
17 * 13 = 221 ≡ 1 (mod 5)
2 * 3 = 6 ≡ 1 (mod 5)
```

### 2.4 幂运算

如果：

$$
a \equiv b \pmod m
$$

那么：

$$
a^k \equiv b^k \pmod m
$$

这就是 RSA 里可以用快速幂：

```python
pow(m, e, n)
```

来计算：

$$
m^e \bmod n
$$

的原因。

### 2.5 负数取模

负数也可以取模：

$$
-a \equiv m-a \pmod m
$$

更准确地说，如果 `a mod m = r`，那么：

```text
(-a) mod m = (m-r) mod m
```

例子：

```text
-3 mod 7 = 4
```

因为：

```text
-3 + 7 = 4
```

### 2.6 除法不能直接做

在普通实数里：

$$
\frac{a}{b}
$$

表示乘以 `1/b`。但在模运算里，不能随便“除以 b”。

模运算中的“除以 b”必须改写为：

$$
a \cdot b^{-1} \pmod m
$$

其中 `b^{-1}` 是 `b` 在模 `m` 意义下的**乘法逆元**，满足：

$$
b \cdot b^{-1} \equiv 1 \pmod m
$$

而这个逆元只有在：

$$
\gcd(b,m)=1
$$

时才一定存在。

例子：

```text
3^{-1} mod 10 = 7
```

因为：

```text
3 * 7 = 21 ≡ 1 (mod 10)
```

但：

```text
2^{-1} mod 10
```

不存在，因为 `gcd(2,10)=2`，没有任何整数 `x` 能让：

```text
2x ≡ 1 (mod 10)
```

---

## 3. 模逆元怎么求

### 3.1 模逆元定义

`a` 关于模 `m` 的逆元记为：

$$
a^{-1} \pmod m
$$

它是满足下面式子的整数：

$$
a\cdot x \equiv 1 \pmod m
$$

也就是：

$$
a\cdot x + m\cdot y = 1
$$

这里的 `x` 就是 `a` 的模逆元。

### 3.2 存在条件

模逆元存在当且仅当：

$$
\gcd(a,m)=1
$$

这也是 RSA 里要求：

$$
\gcd(e,\varphi(n))=1
$$

的原因。只有这样才能求：

$$
d = e^{-1} \pmod{\varphi(n)}
$$

### 3.3 扩展欧几里得算法

扩展欧几里得算法可以求：

$$
ax + my = \gcd(a,m)
$$

当 `gcd(a,m)=1` 时：

$$
ax + my = 1
$$

对两边取模 `m`：

$$
ax \equiv 1 \pmod m
$$

所以：

$$
x \equiv a^{-1} \pmod m
$$

### 3.4 小例子：求 `3^{-1} mod 10`

扩展欧几里得：

```text
10 = 3 * 3 + 1
1 = 10 - 3 * 3
```

所以：

```text
1 = (-3) * 3 + 1 * 10
```

也就是说：

```text
3 * (-3) ≡ 1 (mod 10)
```

把 `-3` 规范成正余数：

```text
-3 mod 10 = 7
```

所以：

```text
3^{-1} mod 10 = 7
```

---

## 4. 同余方程怎么解

同余方程最基础、最常见的是一次同余方程：

$$
ax \equiv b \pmod m
$$

这类方程在 RSA、CRT、线性递推、伪随机数恢复题里非常常见。

### 4.1 一次同余方程的解法

求解：

$$
ax \equiv b \pmod m
$$

步骤：

1. 计算：

   $$
   g = \gcd(a,m)
   $$

2. 判断 `g` 是否整除 `b`

   - 如果：

     $$
     g \nmid b
     $$

     则无解

   - 如果：

     $$
     g \mid b
     $$

     则有 `g` 个模 `m` 意义下的解

3. 两边同时除以 `g`：

   $$
   a' = \frac{a}{g},\quad b'=\frac{b}{g},\quad m'=\frac{m}{g}
   $$

   原方程化成：

   $$
   a'x \equiv b' \pmod {m'}
   $$

4. 此时：

   $$
   \gcd(a',m')=1
   $$

   可以求逆元：

   $$
   (a')^{-1} \pmod {m'}
   $$

5. 得到一个基础解：

   $$
   x_0 \equiv b'\cdot (a')^{-1} \pmod {m'}
   $$

6. 原模数 `m` 下的全部解为：

   $$
   x \equiv x_0 + k\cdot m' \pmod m,\quad k=0,1,\dots,g-1
   $$

### 4.2 例子：解 `14x ≡ 30 (mod 100)`

第一步：

```text
g = gcd(14, 100) = 2
```

因为 `2 | 30`，所以有解，而且有 2 个模 100 意义下的解。

两边除以 2：

```text
7x ≡ 15 (mod 50)
```

求 `7^{-1} mod 50`：

```text
7 * 43 = 301 ≡ 1 (mod 50)
```

所以：

```text
x ≡ 15 * 43 ≡ 645 ≡ 45 (mod 50)
```

因此模 100 下全部解为：

```text
x ≡ 45 (mod 100)
x ≡ 45 + 50 = 95 (mod 100)
```

验证：

```text
14 * 45 = 630 ≡ 30 (mod 100)
14 * 95 = 1330 ≡ 30 (mod 100)
```

### 4.3 特殊情况：`ax ≡ 1 (mod m)`

这就是求逆元：

$$
ax \equiv 1 \pmod m
$$

只有当：

$$
\gcd(a,m)=1
$$

时有解。

RSA 中：

$$
ed \equiv 1 \pmod{\varphi(n)}
$$

就是这个特殊情况。

---

## 5. 多个同余方程：CRT 中国剩余定理

如果题目给出多个余数条件：

$$
\begin{cases}
x \equiv r_1 \pmod {m_1}\\
x \equiv r_2 \pmod {m_2}\\
\dots
\end{cases}
$$

这就是同余方程组。

### 5.1 模数两两互素时

如果 `m_i` 两两互素，设：

$$
M = m_1m_2\dots m_k
$$

对每个方程定义：

$$
M_i = \frac{M}{m_i}
$$

再求：

$$
t_i \equiv M_i^{-1} \pmod {m_i}
$$

那么解为：

$$
x \equiv \sum_{i=1}^{k} r_i M_i t_i \pmod M
$$

### 5.2 例子

求：

$$
\begin{cases}
x \equiv 2 \pmod 3\\
x \equiv 3 \pmod 5\\
x \equiv 2 \pmod 7
\end{cases}
$$

总模数：

```text
M = 3 * 5 * 7 = 105
```

分别计算：

```text
M1 = 105 / 3 = 35,  35^{-1} mod 3 = 2
M2 = 105 / 5 = 21,  21^{-1} mod 5 = 1
M3 = 105 / 7 = 15,  15^{-1} mod 7 = 1
```

所以：

```text
x ≡ 2*35*2 + 3*21*1 + 2*15*1
  ≡ 140 + 63 + 30
  ≡ 233
  ≡ 23 (mod 105)
```

验证：

```text
23 mod 3 = 2
23 mod 5 = 3
23 mod 7 = 2
```

### 5.3 模数不互素时

两个方程：

$$
x \equiv a \pmod m
$$

$$
x \equiv b \pmod n
$$

有解的条件是：

$$
a \equiv b \pmod{\gcd(m,n)}
$$

如果不满足，则无解。

例子：

```text
x ≡ 1 (mod 4)
x ≡ 3 (mod 6)
```

因为：

```text
gcd(4, 6) = 2
1 ≡ 3 (mod 2)
```

所以有解。

但：

```text
x ≡ 1 (mod 4)
x ≡ 2 (mod 6)
```

因为：

```text
1 ≠ 2 (mod 2)
```

所以无解。

---

## 6. RSA 为什么要用模逆元

### 6.1 RSA 参数

RSA 的核心参数是：

```text
p, q: 两个大素数
n = p * q
φ(n) = (p-1)(q-1)
e: 公钥指数，常用 65537
d: 私钥指数
```

`d` 的定义是：

$$
d \equiv e^{-1} \pmod{\varphi(n)}
$$

也就是：

$$
ed \equiv 1 \pmod{\varphi(n)}
$$

等价写法：

$$
ed = 1 + k\varphi(n)
$$

其中 `k` 是某个整数。

### 6.2 加密与解密

加密：

$$
c \equiv m^e \pmod n
$$

解密：

$$
m \equiv c^d \pmod n
$$

代入：

$$
c^d \equiv (m^e)^d \equiv m^{ed} \pmod n
$$

因为：

$$
ed = 1 + k\varphi(n)
$$

所以：

$$
m^{ed} = m^{1+k\varphi(n)} = m\cdot (m^{\varphi(n)})^k
$$

当 `gcd(m,n)=1` 时，根据欧拉定理：

$$
m^{\varphi(n)} \equiv 1 \pmod n
$$

所以：

$$
m\cdot (m^{\varphi(n)})^k \equiv m\cdot 1^k \equiv m \pmod n
$$

这就是 RSA 能正确解密的原因。

!!! note "如果 `m` 和 `n` 不互素怎么办？"
    标准 RSA 的正确性也可以通过分别在模 `p`、模 `q` 下讨论，再用 CRT 合并来证明。CTF 入门分析时，先理解 `gcd(m,n)=1` 的欧拉定理版本通常已经足够。

### 6.3 为什么 `1/65537` 没有意义

在 RSA 里：

$$
e^{-1} \pmod{\varphi(n)}
$$

不是实数倒数：

$$
\frac{1}{65537}
$$

而是要找一个整数 `d`：

$$
65537\cdot d \equiv 1 \pmod{\varphi(n)}
$$

也就是：

$$
65537\cdot d = 1 + k\varphi(n)
$$

由于 `φ(n)` 通常非常大，这个 `d` 往往也是一个很大的整数。

---

## 7. Dino Vault 中的 RSA 结构

题目代码：

```python
transmission_key = getPrime(primesize)
dinosaur_modulation_index = transmission_key * self.vault_key
evergreen_number = 2**16 + 1
resampled_dna = pow(bytes_to_long(self.dna.encode()), evergreen_number, dinosaur_modulation_index)
```

对应到 RSA：

| 代码变量 | RSA 含义 |
|---|---|
| `transmission_key` | 素数 `q` |
| `self.vault_key` | 素数 `p` |
| `dinosaur_modulation_index` | 模数 `n = p*q` |
| `evergreen_number` | 公钥指数 `e = 65537` |
| `bytes_to_long(self.dna.encode())` | 明文整数 `m` |
| `resampled_dna` | 密文整数 `c = m^e mod n` |

漏洞来自同一只恐龙复用 `self.vault_key`：

$$
n_1 = p q_1,\quad n_2 = p q_2
$$

因此：

$$
\gcd(n_1,n_2)=p
$$

拿到 `p` 后就能分解 `n_1`，再求：

$$
d = e^{-1} \pmod{(p-1)(q_1-1)}
$$

最终解密：

$$
m = c_1^d \bmod n_1
$$

---

## 8. 常见误区总结

### 误区 1：`e^{-1}` 等于 `1/e`

错误。RSA 里的 `e^{-1}` 是模逆元，不是小数倒数。

正确理解：

```text
d 是整数，并且 e*d ≡ 1 (mod φ(n))
```

### 误区 2：模运算里可以随便除法

错误。模运算中除法必须转成乘以逆元，而且逆元不一定存在。

```text
a / b mod m  应理解为  a * b^{-1} mod m
```

前提是：

```text
gcd(b, m) = 1
```

### 误区 3：看到 `pow(x, y, z)` 就一定是 RSA

不一定。`pow(x, y, z)` 只是模幂运算。判断 RSA 还要看：

- 模数是否是两个大素数乘积
- 指数是否是 RSA 公钥指数，如 65537
- 明文是否被转成整数再模幂

Dino Vault 之所以能判断为 RSA，是因为这些条件同时出现。

### 误区 4：只要 `e=65537` 就安全

错误。`e=65537` 是常见安全参数之一，但安全性还依赖：

- 模数不能共享素因子
- 素数必须随机且独立
- 不能使用裸 RSA 加密结构化明文
- 实际协议应使用 OAEP 等安全填充

---

## 9. 快速代码片段

### Python：求模逆元

```python
d = pow(e, -1, phi)
```

或者：

```python
from Crypto.Util.number import inverse
d = inverse(e, phi)
```

### Go：求模逆元

```go
d := new(big.Int).ModInverse(e, phi)
if d == nil {
    panic("inverse does not exist")
}
```

### Python：解一次同余方程

```python
from math import gcd

def solve_linear_congruence(a, b, m):
    g = gcd(a, m)
    if b % g != 0:
        return []

    a1, b1, m1 = a // g, b // g, m // g
    inv = pow(a1, -1, m1)
    x0 = (b1 * inv) % m1
    return [(x0 + k * m1) % m for k in range(g)]

print(solve_linear_congruence(14, 30, 100))
# [45, 95]
```

