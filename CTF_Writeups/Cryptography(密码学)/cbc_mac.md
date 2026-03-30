# CBC-MAC 知识点常见问题解答

> 本文档是 [Echoes of the Serpent Writeup](NovruzCTF_Echoes_of_the_Serpent.md) 的补充知识点，以 Q&A 形式解答 CBC-MAC 长度扩展攻击中的常见疑问。

---

## 如何复用本文作为 FAQ 模板

- 标题改为：`[知识点] 知识点常见问题解答`
- 第一段写明：这是哪个 Writeup 的知识点补充，并给出反向链接
- 至少保留 4 个核心问题：**为什么成立 / 关键参数作用 / 公式符号含义 / 常见误区**
- 每个问题都用「一句话结论 + 关键推导或示例」的结构，避免只给结论

## Q1：不知道密钥，为什么还能伪造 MAC？

CBC-MAC 长度扩展攻击**完全不依赖密钥**。

攻击只需要服务器返回的两个已知 MAC 值：

1. 服务器给你 $T_1 = \text{MAC}(\text{"hello\_world"})$ 和 $T_2 = \text{MAC}(\text{"get\_flag"})$
2. 构造 `forged_msg = pad("hello_world") || (T₁ ⊕ pad("get_flag"))`
3. 提交 `forged_msg` + $T_2$ 即可

XOR 的数学性质保证 MAC 验证一定通过——$T_1$ 在 CBC 链式计算中与自身异或消去，无需知道密钥。

---

## Q2：如何看出 IV 全零？IV 有什么作用？

**IV 在哪里看出来的**

源码中：

```python
IV = bytes(16)  # 16 个 \x00 字节
```

Python 中 `bytes(16)` 生成 16 字节全零 `\x00\x00...\x00`，不是数字 16。

**IV 的作用**

IV（Initialization Vector，初始化向量）是 CBC 模式中第一个明文块加密前的 XOR 输入：

$$C_1 = E_K(M_1 \oplus IV), \quad C_2 = E_K(M_2 \oplus C_1), \quad \dots$$

它的目的是让相同明文在不同 IV 下产生不同密文，防止攻击者识别重复模式。

**对本题的影响**

IV = 0 时，第一块简化为 $C_1 = E_K(M_1 \oplus 0) = E_K(M_1)$，XOR 0 等于什么都没做。不过对长度扩展攻击来说，IV 是否全零不影响攻击成立——攻击利用的是 CBC 链式结构，IV 全零只是让分析更直观。

---

## Q3：pad() 是什么意思？

`pad()` 就是源码里的 `zero_pad` 函数——把数据用 `\x00` 补齐到 16 字节的倍数。

```text
"hello_world" → 11 字节 + 5 个 \x00 = 16 字节
"get_flag"    →  8 字节 + 8 个 \x00 = 16 字节
```

AES 是分组密码，每块固定 16 字节，不够就必须补齐。Writeup 中的 `pad(M₁)` 就是指补零后的完整块。

---

## Q4：为什么 MAC(M₁ || M₂) = C₂？

因为 CBC-MAC 的定义就是**取 CBC 加密后的最后一个密文块**：

```python
def cbc_mac(data: bytes) -> bytes:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ct = cipher.encrypt(zero_pad(data))
    return ct[-16:]  # 取最后 16 字节 = 最后一个密文块
```

对于两块消息 $M_1 \| M_2$，CBC 加密产生 $C_1, C_2$，`ct[-16:]` 取的就是 $C_2$。

直观理解 CBC 链式过程：

$$\boxed{M_1} \xrightarrow{\oplus\, IV} \boxed{E_K} \rightarrow C_1 \xrightarrow{\oplus\, M_2} \boxed{E_K} \rightarrow C_2$$

- 1 块消息：MAC = $C_1$
- 2 块消息：MAC = $C_2$
- N 块消息：MAC = $C_N$

永远取最后一个密文块作为 MAC 值。

---

## Q5：什么叫做"两块消息"，是如何拼接的？

**"块"就是 AES 的固定大小：16 字节。** AES 一次只能处理 16 字节，所以消息被切成 16 字节一块。

**单块消息**

```text
[h e l l o _ w o r l d \0 \0 \0 \0 \0]
|<------------- 16 字节 ------------->|
                 M₁
```

**两块消息（伪造的 32 字节消息）**

```text
块1: [h e l l o _ w o r l d \0 \0 \0 \0 \0]     ← pad("hello_world")
块2: [10 89 7b 80 7f 77 71 76 b9 74 86 4b ...]   ← T₁ ⊕ pad("get_flag")
```

`||` 就是首尾拼接，两块直接接在一起变成 32 字节。CBC 处理时：

```text
第一块：C₁ = E_K(M₁ ⊕ IV)       ← 加密第一块
第二块：C₂ = E_K(M₂ ⊕ C₁)       ← 链式：上一块密文 XOR 后再加密
MAC = C₂                          ← 取最后一块
```

每一块都把前一块的加密结果 XOR 进来再加密，这就是"链式"（Chain）的含义。

---

## Q6：$E_K$ 是什么操作？

$E_K$ 是 **AES 加密**，不是 XOR。CBC 每一块有两步操作：

1. **XOR（异或）** — 把明文和前一块密文混合
2. **$E_K$（AES 加密）** — 用密钥 $K$ 加密混合后的结果

```text
第一块：
  临时值 = M₁ ⊕ IV        ← 第一步：XOR
  C₁    = E_K(临时值)      ← 第二步：AES 加密

第二块：
  临时值 = M₂ ⊕ C₁        ← 第一步：XOR
  C₂    = E_K(临时值)      ← 第二步：AES 加密
```

$E_K$ 就是 `AES.new(KEY, ...)` 做的事——接收 16 字节输入，通过密钥 $K$ 做一系列置换和替换运算，输出 16 字节密文。没有密钥无法逆推。

但攻击不需要知道 $E_K$ 内部做了什么，只需要利用链式结构：已知 $T_1 = E_K(M_1)$，构造下一块输入时用 XOR 把 $T_1$ 消掉就行。

---

## Q7：MAC(M₁) 就是对 M₁ 进行 AES 加密吗？

**在本题中是的**——因为 $M_1$ 只有一块且 IV 全零：

$$\text{MAC}(M_1) = E_K(M_1 \oplus \underbrace{0\dots0}_{IV}) = E_K(M_1)$$

但 MAC 和 $E_K$ 不是同一个概念：

- $E_K$ — AES 加密**一个** 16 字节块（底层操作）
- MAC — 对**整条消息**（可能多块）做 CBC 链式加密后取最后一块（上层协议）

当消息有两块时：

$$\text{MAC}(M_1 \| M_2) = E_K(M_2 \oplus E_K(M_1))$$

这就不是简单的"一次 AES 加密"了，而是两次 $E_K$ 加上 XOR。

**伪造的数学原理：**

$$\underbrace{(T_1 \oplus \text{pad}(M_2))}_{\text{构造的第二块}} \oplus\ T_1 = \text{pad}(M_2) \oplus \underbrace{T_1 \oplus T_1}_{= 0} = \text{pad}(M_2)$$

$T_1$ 与自身异或消去，剩下 $\text{pad}(M_2)$ 送进 $E_K$ 得到 $T_2$，伪造成功。

---

## 可复制模板（空白版）

```markdown
# [知识点] 知识点常见问题解答

> 本文档是 [对应题目 Writeup](./[writeup_file].md) 的补充知识点，以 Q&A 形式回答常见问题。

---

## Q1：为什么 [攻击/机制] 可以成立？
[一句话结论 + 最关键公式/推导]

## Q2：[关键参数] 在这里起什么作用？
[参数定义 + 对结果的实际影响 + 边界条件]

## Q3：[符号/函数] 具体表示什么？
[拆分步骤解释，避免只给符号]

## Q4：这类题最常见的误区是什么？
[误区 + 正确理解 + 一个反例（可选）]
```
