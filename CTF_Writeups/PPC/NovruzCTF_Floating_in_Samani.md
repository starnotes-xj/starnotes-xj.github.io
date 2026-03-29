# novruzCTF - XOR42 (Misc/Math)

## 题目信息

- **题目名称**: XOR42（Floating in Samani above Metra Veehkim）
- **类别**: Misc / Math
- **难度**: 困难
- **题目描述**: Floating in samani above Metra Veehkim, you find yourself in a strange place amongst numbers and arithmetic operations.
- **连接**: `nc tcp.canyouhack.org 10091`
- **附件**: `e8f04de8-b931-48d5-a462-f07bb37a648f.py`
- **状态**: 已解

## 解题过程

### 1. 分析题目源码

```python
class CheckVisitor(ast.NodeVisitor):
    def visit_Name(self, node):
        if node.id not in ['a', 'b']:
            raise ValueError(f"accessing {node.id} is not allowed")

    def generic_visit(self, node):
        if not (isinstance(node, ast.Module) or
                isinstance(node, ast.Expr) or
                isinstance(node, ast.BinOp) or
                isinstance(node, ast.Add) or
                isinstance(node, ast.Sub) or
                isinstance(node, ast.Div) or
                isinstance(node, ast.Mult) or
                isinstance(node, ast.Load) or
                isinstance(node, ast.Name) or
                isinstance(node, ast.Constant)):
            raise ValueError(f"node {type(node)} is not allowed")

def main():
    code = input()
    visitor = CheckVisitor()
    visitor.visit(ast.parse(code))
    for a in range(256):
        assert (a ^ 42) == int(eval(code))
    print(os.getenv("FLAG"))
```

**关键约束**：

| 约束 | 说明 |
|------|------|
| 允许的 AST 节点 | Module, Expr, BinOp, Add, Sub, Div, Mult, Load, Name, Constant |
| 允许的变量名 | 仅 `a` 和 `b` |
| 验证方式 | `int(eval(code)) == a ^ 42`，对所有 `a ∈ [0, 255]` |
| 不允许 | 函数调用、位运算、比较、下标、属性访问、一元运算符等 |

核心挑战：**用纯算术表达式（+, -, *, /）和常数表示 XOR 运算**。

### 2. 关键洞察：IEEE 754 浮点取整技巧

题目名称 "**Floating** in samani above **Metra Veehkim**" 暗示了浮点数（Float）。

核心思路：Python 的 `eval()` 使用 **float64 运算**（IEEE 754 双精度），我们可以利用浮点数的精度特性来实现 `FLOOR` 函数，进而逐位计算 AND 和 XOR。

#### 2.1 用算术实现 FLOOR

IEEE 754 双精度浮点数有 52 位尾数。当一个数落在 $[2^{52}, 2^{53})$ 区间时，浮点数的精度恰好为 1.0 —— 即该范围内的浮点数只能表示整数。

设魔法常数 $C = 3 \times 2^{51} = 6755399441055744$，则：

$$\text{FLOOR}(x) = x - \frac{63}{128} + C - C$$

**原理**：
- $x + C$ 将结果推入 $[2^{52}, 2^{53})$ 区间，浮点数自动四舍五入到最近整数
- 偏移量 $-63/128$ 确保所有可能的小数部分（1/64 的倍数）都被正确向下取整
- 最后减去 $C$ 还原到原始量级

#### 2.2 用 FLOOR 实现 AND（逐位）

对于单个 bit 位置 $k$：

$$\text{bit}_k(a) = \text{FLOOR}(a / 2^k) \mod 2 = \text{FLOOR}(a / 2^k) - 2 \cdot \text{FLOOR}(a / 2^{k+1})$$

两个数的 AND 在第 $k$ 位：$\text{bit}_k(a) \cdot \text{bit}_k(42)$

但 42 是常数，我们只需处理 42 中为 1 的位。

#### 2.3 用 AND 实现 XOR

$$a \oplus 42 = a + 42 - 2 \cdot (a \text{ AND } 42)$$

这是因为：对每一位，`a + b = (a XOR b) + 2*(a AND b)`。

### 3. 展开 42 的二进制

$42 = 0b00101010$，在位置 1, 3, 5 处有置位。

逐位展开 $a \text{ AND } 42$：

$$a \text{ AND } 42 = 2 \cdot \text{bit}_1(a) + 8 \cdot \text{bit}_3(a) + 32 \cdot \text{bit}_5(a)$$

代入 XOR 公式并化简：

$$a \oplus 42 = a + 42 - 4 \cdot \text{FLOOR}(a/2) + 8 \cdot \text{FLOOR}(a/4) - 16 \cdot \text{FLOOR}(a/8) + 32 \cdot \text{FLOOR}(a/16) - 64 \cdot \text{FLOOR}(a/32) + 128 \cdot \text{FLOOR}(a/64)$$

### 4. 最终 Payload

将 FLOOR 展开，得到完整的纯算术表达式：

```
a + 42
 - 4 * (a / 2 - 63 / 128 + 6755399441055744 - 6755399441055744)
 + 8 * (a / 4 - 63 / 128 + 6755399441055744 - 6755399441055744)
 - 16 * (a / 8 - 63 / 128 + 6755399441055744 - 6755399441055744)
 + 32 * (a / 16 - 63 / 128 + 6755399441055744 - 6755399441055744)
 - 64 * (a / 32 - 63 / 128 + 6755399441055744 - 6755399441055744)
 + 128 * (a / 64 - 63 / 128 + 6755399441055744 - 6755399441055744)
```

**表达式长度**：仅约 400 字节（对比多项式插值方案的 317KB）。

### 5. Go TCP 客户端提交

```go
func main() {
    addr := "tcp.canyouhack.org:10091"
    conn, _ := net.DialTimeout("tcp", addr, 30*time.Second)
    defer conn.Close()

    // payload 直接内嵌在代码中，无需外部文件
    payload := "a + 42" +
        " - 4 * (a / 2 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
        " + 8 * (a / 4 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
        " - 16 * (a / 8 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
        " + 32 * (a / 16 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
        " - 64 * (a / 32 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
        " + 128 * (a / 64 - 63 / 128 + 6755399441055744 - 6755399441055744)"

    // 读取 banner，发送 payload，读取 flag
    fmt.Fprintf(conn, "%s\n", payload)
}
```

## 漏洞分析

### 核心思路

本题的关键在于题目名称的暗示 —— **Floating**（浮点数）。

Python 的 `/` 运算符返回 float64，而 IEEE 754 双精度浮点数在特定区间内具有整数精度的特性。利用这一特性，可以用纯算术构造 FLOOR 函数，进而实现位运算。

**数学链条**：

```
FLOOR (IEEE 754 精度特性)
  → 逐位提取 (FLOOR + 除法)
    → AND (逐位乘积)
      → XOR = a + b - 2*(a AND b)
```

### 为什么 FLOOR 技巧有效？

| 组件 | 公式 | 原理 |
|------|------|------|
| 魔法常数 C | $3 \times 2^{51}$ | 将加数推入 $[2^{52}, 2^{53})$，float64 精度 = 1.0 |
| 偏移量 | $-63/128$ | 修正四舍五入为向下取整（$63/128 = 0.4921875$） |
| FLOOR(x) | $x - 63/128 + C - C$ | 加 C 触发舍入，减 C 还原 |

### 对比方案

| 方案 | 表达式大小 | 复杂度 | 可行性 |
|------|-----------|--------|--------|
| **IEEE 754 FLOOR 技巧** | ~400 字节 | 简洁优雅 | **正确解法** |
| Newton 多项式插值 | ~317 KB | 需要精确大整数运算 | 可行但笨重 |
| 查表/穷举 | 不适用 | 无法在 AST 约束下实现 | 不可行 |

## 知识点总结

### IEEE 754 双精度浮点数

- **尾数位数**: 52 位（隐含 1 位共 53 位）
- **关键区间**: $[2^{52}, 2^{53})$ 内浮点数只能表示整数
- **魔法常数**: $C = 3 \times 2^{51} = 6755399441055744$，使得 $x + C$ 落入该区间
- **取整行为**: 浮点加法自动执行 "round to nearest even"

### XOR 的算术分解

- **XOR 公式**: $a \oplus b = a + b - 2(a \text{ AND } b)$
- **AND 逐位计算**: 利用 FLOOR 和除法提取每一位
- **位提取**: $\text{bit}_k(a) = \text{FLOOR}(a/2^k) - 2 \cdot \text{FLOOR}(a/2^{k+1})$

### Python AST 约束绕过

- 所有操作均为 `BinOp`（+, -, *, /）和 `Constant`
- 无需函数调用、位运算或一元运算符
- 利用 Python `/` 运算符返回 float 的特性

## 使用的工具

| 工具 | 用途 |
|------|------|
| Go (net, bufio) | TCP 客户端，连接服务器提交表达式 |
| IEEE 754 数学 | 浮点精度特性构造 FLOOR 函数 |

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Floating in Samani.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Floating in Samani.py`

## 命令行提取关键数据（无 GUI）

```bash
# 直接连接题目服务，拿到输入提示
nc tcp.canyouhack.org 10091
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Crypto 和通用工具推荐。本题属于 Misc/Math 类型，核心在数学推导。

### 1. Z3 Solver — SMT 求解器（辅助验证）

[Z3](https://github.com/Z3Prover/z3) 是微软开源的 SMT 求解器，虽然不能直接生成 Python 表达式，但可以验证数学推导是否正确。

**安装：**
```bash
pip install z3-solver
```

**详细操作步骤：**

**Step 1：验证 XOR 分解公式**
```python
from z3 import *

a = BitVec('a', 8)
# 验证: a ^ 42 == a + 42 - 2 * (a & 42)
prove(a ^ 42 == a + 42 - 2 * (a & 42))
# 输出: proved
```

**Step 2：验证位提取公式**
```python
# 验证: bit_k(a) = floor(a/2^k) - 2*floor(a/2^(k+1))
a = BitVec('a', 16)
for k in [1, 3, 5]:  # 42 的置位位
    bit_k = (a >> k) & 1
    floor_k = URem(a, 2**(k+1)) // (2**k)  # 等价于 floor(a/2^k) mod 2
    prove(bit_k == floor_k)
```

**优势**：快速验证数学等价性，确认公式推导无误后再构造表达式。

---

### 2. SageMath — 符号计算

SageMath 可以辅助推导和简化数学表达式。

```python
sage: var('a')
sage: # 42 = 0b101010, 置位位: 1, 3, 5
sage: # XOR 公式展开
sage: xor_expr = a + 42 - 4*floor(a/2) + 8*floor(a/4) - 16*floor(a/8) + 32*floor(a/16) - 64*floor(a/32) + 128*floor(a/64)
sage: # 验证
sage: all(int(xor_expr.subs(a=i)) == i ^^ 42 for i in range(256))
# True
```

---

### 3. Pwntools — 远程交互提交

[Pwntools](https://github.com/Gallopsled/pwntools) 是 CTF 远程交互的标准工具，比手写 TCP 客户端更方便。

**安装：**
```bash
pip install pwntools
```

**详细操作步骤：**

```python
from pwn import *

# Step 1: 连接服务器
r = remote('tcp.canyouhack.org', 10091)

# Step 2: 读取 banner
banner = r.recvuntil(b'>')
log.info(f"Banner: {banner}")

# Step 3: 构造并发送 payload
C = 6755399441055744
payload = f"a + 42"
for k in [1, 3, 5]:  # 42 的置位位
    sign = "-" if True else "+"
    coeff = 2 ** (k + 1)
    divisor = 2 ** k
    payload += f" - {coeff} * (a / {divisor} - 63 / 128 + {C} - {C})"

r.sendline(payload.encode())

# Step 4: 接收 flag
flag = r.recvall(timeout=5)
log.success(f"Flag: {flag}")
```

**优势**：`remote()` 一行连接，`sendline()` / `recvall()` 简化交互，`log` 格式化输出。

---

### 4. CyberChef — 快速 XOR 计算验证

```
# 在 CyberChef 中验证 XOR 结果
Input: 任意字节
操作: XOR({'option':'Decimal','string':'42'})
# 验证手动计算的结果是否正确
```

---

### 工具对比总结

| 工具 | 适用阶段 | 优点 |
|------|---------|------|
| **Z3 Solver** | 验证数学公式 | 形式化证明，100% 正确性保证 |
| **SageMath** | 符号推导、简化 | 数学表达式操作方便 |
| **Pwntools** | 远程交互提交 | CTF 标准库，比手写 TCP 简洁 |
| **CyberChef** | 快速 XOR 验证 | 在线操作，无需编程 |
| **Go TCP 客户端** | 远程提交 | 性能好，但代码量较多 |

**推荐流程**：Z3 验证 XOR 分解公式 → SageMath 推导简化 → Python 构造表达式 → Pwntools 提交 → 5 分钟内完成。

> **注意**：本题的核心挑战是**数学推导**（IEEE 754 FLOOR 技巧），工具只能辅助验证和提交。关键洞察（利用浮点精度实现 FLOOR）需要人脑完成。

## 解题流程图

```
分析源码约束：只允许 +, -, *, / 和常数
    │
    ▼
题目名暗示 "Floating" → 浮点数技巧
    │
    ▼
IEEE 754: 在 [2^52, 2^53) 区间，float64 精度 = 1.0
    │
    ▼
构造 FLOOR(x) = x - 63/128 + C - C  (C = 3×2^51)
    │
    ▼
XOR 分解: a ^ 42 = a + 42 - 2*(a AND 42)
    │
    ▼
42 = 0b101010 → 展开位 1, 3, 5 的 AND 计算
    │
    ▼
生成纯算术表达式 (~400 字节)
    │
    ▼
Go TCP 客户端发送 payload → 获取 Flag
```
