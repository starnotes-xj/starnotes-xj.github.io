# NovruzCTF - Ritual (Reverse Engineering)

## 题目信息

- **比赛**: NovruzCTF
- **题目**: 古老的仪式咒语 / Ritual
- **类型**: Reverse Engineering
- **附件**: `ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin`
- **Flag格式**: `novruzCTF{}` (注意大写 CTF)
- **状态**: 已解

**题目描述**:
> 诺鲁孜节的三个星期二已经过去了。水已净化，火已点燃，风已吹散灰烬。但似乎还缺少些什么。一段古老的仪式咒语隐藏在代码深处。找到它，完成仪式。

## Flag

```
novruzCTF{buta-tonq-kosa}
```

**注意**：Flag 格式为 `novruzCTF{}`（大写 CTF），程序内硬编码了 `novruzCTF{` 前缀校验（Go `strings.HasPrefix` 大小写敏感）。

## 解题过程

### 1. 文件识别

```
ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked,
BuildID[sha1]=f2a982a78430494b59836b213ba2530d68fee252, stripped
```

Go 1.25.8 编译的静态链接 Linux ELF 二进制，已 strip（无调试符号）。
编译参数包含 `-ldflags="-w -s"` 进一步移除了调试信息。
源码路径泄露：`/home/abdullaxows/Documents/novruzctf_2026/murad/main.go`

### 2. 字符串分析

通过 `grep -ao` 提取二进制中的可打印字符串，发现关键信息：

**程序流程相关字符串：**
- `Enter the ritual phrase:` — 输入提示
- `Three Tuesdays require three parts.` — 输入需要 3 个部分
- `The ritual format is wrong.` — 格式错误
- `Fire refused to burn.` / `Water rejected your offering.` / `Wind scattered the ashes.` — 三个阶段的失败消息
- `[+] All three Tuesdays have been honored.` — 全部通过
- `[+] The ritual is complete.` — 仪式完成
- `[+] Novruz accepted your phrase.` — 接受

**函数名（Go 符号保留在 pclntab 中）：**
```
main.main
main.intro
main.fail
main.stageFire
main.stageWater  (名称存在但函数被内联到 main)
main.stageWind
```

**SQL 注入相关（无关）：**
```sql
INSERT INTO users VALUES ('revker', 'kerrev', 'Cup{xxx...}')
```

### 3. 解析 Go pclntab 定位函数地址

Go 二进制即使 stripped，仍保留 `pclntab`（PC-Line Number Table），其中包含函数名和地址映射。

通过解析 `moduledata` 结构（位于 ELF 数据段 `0x16a240`），找到：
- `pclntable`: ptr=`0x53f880`
- `ftab` (函数索引表): ptr=`0x53f880`, len=1887
- `funcnametab`: ptr=`0x4eb960`
- `textStart`: `0x401000`

遍历 ftab 提取 `main.*` 函数地址：

| 函数 | 虚拟地址 | 文件偏移 | 大小 |
|------|---------|---------|------|
| `main.main` | `0x49b500` | `0x9b500` | 1312 字节 |
| `main.intro` | `0x49ba20` | `0x9ba20` | 256 字节 |
| `main.fail` | `0x49bb20` | `0x9bb20` | 256 字节 |
| `main.stageFire` | `0x49bc20` | `0x9bc20` | 160 字节 |
| `main.stageWind` | `0x49bcc0` | `0x9bcc0` | 128 字节 |

注意：`stageWater` 不在函数表中 — 它被 **内联** 到了 `main.main` 中。

### 4. 手动反汇编分析

由于环境限制无法安装反汇编工具（capstone），采用**手动 x86-64 字节码解码**。

#### main.main 关键流程

```
1. 调用 intro() 打印欢迎信息
2. 读取用户输入 (fmt.Scan)
3. 去除尾部换行符 (strings.TrimSuffix)
4. 以 "-" 为分隔符分割输入 (strings.SplitN)
5. 检查是否恰好 3 个部分，每个部分长度为 4
6. stageWater: 内联验证 parts[0]
7. stageFire:  调用验证 parts[1]
8. stageWind:  调用验证 parts[2]
9. 打印成功信息
```

**分隔符确认**：在 `main.main` 中，`strings.SplitN` 调用前通过 `LEA rcx, [rip+0x23ce5]` 加载分隔符字符串指针，指向 rodata 中的 `0x2d` = `'-'`。

#### stageWater（内联在 main 中）

从 `main.main` 偏移 `0x2c0` 处开始，使用**索引置换 + 加法校验**：

```
目标数组 [rsp+0x30]: [0x79, 0x64, 0x68, 0x76] = ['y', 'd', 'h', 'v']
密钥数组 [rsp+0x34]: [0x05, 0x02, 0x07, 0x01]
索引数组 [rsp+0x48]: [2, 0, 3, 1]  (置换顺序)
```

验证逻辑（4 次迭代）：

$$\text{input}[\text{index}[i]] + \text{key}[i] = \text{target}[i]$$

求解：
```
i=0: input[2] + 0x05 = 0x79 → input[2] = 0x74 = 't'
i=1: input[0] + 0x02 = 0x64 → input[0] = 0x62 = 'b'
i=2: input[3] + 0x07 = 0x68 → input[3] = 0x61 = 'a'
i=3: input[1] + 0x01 = 0x76 → input[1] = 0x75 = 'u'
```

**stageWater 答案：`buta`**

#### stageFire（0x49bc20，160 字节）

使用**累加器校验 + 线性方程组**：

**第一层：旋转异或累加器**
```
acc = 0x45
for i in range(4):
    acc = ROL32(acc, 2)  # 循环左移 2 位
    acc ^= input[i]
    acc += (i + 1)
assert acc == 0x5f09
```

**第二层：字节对约束**

$$\text{input}[1] + \text{input}[0] \times 2 = \texttt{0x157}\ (343)$$

$$\text{input}[0] - \text{input}[1] = 5$$

$$\text{input}[2] + \text{input}[3] \times 2 = \texttt{0x150}\ (336)$$

$$\text{input}[3] - \text{input}[2] = 3$$

求解线性方程组：

**第一组**：$b_0 - b_1 = 5$，$b_1 + 2b_0 = 343$
$$\Rightarrow 3b_1 = 333,\quad b_1 = 111 = \text{'o'},\quad b_0 = 116 = \text{'t'}$$

**第二组**：$b_3 - b_2 = 3$，$b_2 + 2b_3 = 336$
$$\Rightarrow 3b_2 = 330,\quad b_2 = 110 = \text{'n'},\quad b_3 = 113 = \text{'q'}$$

验证累加器：`0x5f09` ✓

**stageFire 答案：`tonq`**

#### stageWind（0x49bcc0，128 字节）

使用**多重约束方程组**：

$$\text{input}[0] + \text{input}[1] = \texttt{0xDA}\ (218)$$

$$\text{input}[0] - \text{input}[1] = -4 \quad (\text{即 } \text{input}[1] = \text{input}[0] + 4)$$

$$\text{input}[2] + \text{input}[3] = \texttt{0xD4}\ (212)$$

$$\text{input}[2] \oplus \text{input}[3] = \texttt{0x12}\ (18)$$

$$\text{input}[3] + \text{input}[0] = \texttt{0xCC}\ (204)$$

求解：

$$b_0 + (b_0 + 4) = 218 \Rightarrow b_0 = 107 = \text{'k'},\quad b_1 = 111 = \text{'o'}$$

$$b_3 = 204 - 107 = 97 = \text{'a'}$$

$$b_2 = 212 - 97 = 115 = \text{'s'}$$

验证：$115 \oplus 97 = 18$ ✓

**stageWind 答案：`kosa`**

### 5. 组合最终答案

```
Ritual phrase: buta-tonq-kosa
Flag: novruzCTF{buta-tonq-kosa}
```

## 命令行提取关键数据（无 GUI）

**字符串筛选**：
```bash
strings -a -n 4 ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin | rg "ritual|Tuesday|Novruz"
```

**Radare2 快速定位主流程**：
```bash
r2 -A ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin
iz~ritual
afl~main
pdf @ main.main
```

## 漏洞/知识点分析

### Go 逆向特点
- **pclntab 保留**：即使 stripped，Go 二进制仍保留 `pclntab` 中的函数名称信息，可用于定位所有函数
- **moduledata 结构**：位于 `.data` 段，包含 `ftab`（函数地址表）和 `funcnametab`（函数名表）的指针
- **函数内联**：`stageWater` 被内联到 `main.main` 中，不出现在函数表中
- **寄存器调用约定**：Go 1.17+ 使用寄存器传参（RAX=第一个参数，RBX=第二个参数等）

### 数学约束求解
- **线性方程组**：stageFire 使用两个变量的线性方程对，直接代入消元即可求解
- **混合约束**：stageWind 结合加法、减法和 XOR 约束，通过逐步代入求解
- **旋转异或校验**：stageFire 的累加器使用 ROL + XOR + ADD 组合，增加暴力破解难度
- **索引置换**：stageWater 通过重新排列字节检查顺序增加逆向难度

### 诺鲁孜文化背景
- **buta** (布塔) — 佩斯利花纹/树枝装饰，阿塞拜疆的国家象征，诺鲁孜装饰元素
- **tonq** (通加勒) — 篝火，诺鲁孜节跳火传统 (Chaharshanbe Suri)
- **kosa** — 风，吹散旧年灰烬的仪式
- 三个"星期二" (Su Chershenbesi) — 诺鲁孜节前的三个星期二分别代表水、火、风

## 知识点
- **Go pclntab** — stripped 二进制仍保留函数名与地址映射
- **moduledata 结构** — 通过 ftab/funcnametab 恢复符号
- **函数内联** — 关键校验逻辑可能被内联到 main
- **约束求解** — 线性方程组与 XOR 约束组合求解

## 使用的工具

- **Python** — ELF 解析、pclntab 解析、moduledata 遍历
- **grep -ao** — 二进制字符串提取（替代 strings 命令）
- **手动 x86-64 反汇编** — 在无 capstone/IDA 环境下手动解码机器码

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruz Ritual.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruz Ritual.py`

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的逆向工程工具推荐。本题手动反汇编耗时较长，使用以下工具可以大幅提升效率。

### 1. Ghidra — 反编译直接看伪代码（推荐首选）

[Ghidra](https://ghidra-sre.org/) 是 NSA 开源的免费逆向工程框架，支持 Go 二进制分析。

**安装：**
```bash
# 下载安装 Ghidra（需要 JDK 17+）
# https://ghidra-sre.org/ 下载最新版本
# 解压后运行 ghidraRun
```

**详细操作步骤：**

**Step 1：导入二进制文件**
1. 打开 Ghidra → File → New Project → 创建项目
2. File → Import File → 选择 `ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin`
3. Ghidra 自动识别为 ELF 64-bit x86-64
4. 双击文件打开 CodeBrowser

**Step 2：自动分析**
1. 弹出 "Analyze" 对话框 → 点击 "Yes"
2. 保持默认分析选项（确保勾选 "Decompiler Parameter ID"）
3. 等待分析完成（Go 静态链接二进制较大，约 1-3 分钟）

**Step 3：恢复 Go 函数名**
- Ghidra 会自动解析 Go 的 `pclntab`，在 Symbol Tree 中可以看到 `main.main`、`main.stageFire`、`main.stageWind` 等函数名
- 如果未自动恢复，安装 [GhidraGo](https://github.com/padorka/GhidraGo) 插件辅助

**Step 4：反编译 stageFire（关键）**
1. 在 Symbol Tree 中搜索 `stageFire` → 双击跳转
2. 右侧 Decompiler 窗口直接显示伪代码，类似：
```c
// Ghidra 反编译伪代码（示意）
bool main.stageFire(byte *input, int len) {
    if (len != 4) return false;

    // 累加器校验
    uint acc = 0x45;
    for (int i = 0; i < 4; i++) {
        acc = ROL(acc, 2);
        acc ^= input[i];
        acc += (i + 1);
    }
    if (acc != 0x5f09) return false;

    // 线性方程约束
    if (input[1] + input[0] * 2 != 0x157) return false;
    if (input[0] - input[1] != 5) return false;
    if (input[2] + input[3] * 2 != 0x150) return false;
    if (input[3] - input[2] != 3) return false;

    return true;
}
```
3. 从伪代码中可以**直接读取所有约束条件**，无需手动解码字节码

**Step 5：反编译 stageWind**
1. 同样搜索 `stageWind` → 查看反编译结果
2. 直接看到 5 个约束方程，手动求解即可

**Step 6：分析 main.main 中内联的 stageWater**
1. 跳转到 `main.main` 函数
2. 在反编译窗口中找到 `strings.SplitN` 调用后的代码段
3. 内联的 stageWater 验证逻辑会显示为循环结构，包含目标数组、密钥数组和索引数组

**优势**：无需手动解码机器码，反编译伪代码直接暴露所有约束条件，从导入到求解约 10 分钟。

---

### 2. Radare2 — 命令行快速分析

[Radare2](https://github.com/radareorg/radare2) 是一个强大的 CLI 逆向框架，适合快速查看函数结构。

**安装：**
```bash
# Linux/macOS
git clone https://github.com/radareorg/radare2 && cd radare2 && sys/install.sh

# 或使用包管理器
brew install radare2        # macOS
sudo apt install radare2    # Debian/Ubuntu
```

**详细操作步骤：**

**Step 1：加载并分析二进制**
```bash
r2 -A ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin
# -A 自动执行 aaa（分析所有函数、引用、字符串等）
# Go 二进制分析较慢，等待约 30 秒
```

**Step 2：列出 main 包函数**
```bash
[0x00401000]> afl~main.
# 输出类似：
# 0x0049b500  1312  main.main
# 0x0049ba20   256  main.intro
# 0x0049bb20   256  main.fail
# 0x0049bc20   160  main.stageFire
# 0x0049bcc0   128  main.stageWind
```

**Step 3：反汇编 stageFire**
```bash
[0x00401000]> pdf @main.stageFire
# pdf = Print Disassembly Function
# 显示完整的 x86-64 汇编指令
# 从中可以看到 ROL、XOR、CMP 等关键指令和立即数
```

**Step 4：反汇编 stageWind**
```bash
[0x00401000]> pdf @main.stageWind
# 显示加法、减法、XOR 比较的汇编指令
# 立即数 0xDA, 0xD4, 0x12, 0xCC 直接可见
```

**Step 5：查看 main.main 中的字符串引用**
```bash
[0x00401000]> pdf @main.main
# 查看完整的 main 函数，包括内联的 stageWater
# 关注 MOV 指令加载的常量值

# 或者直接搜索字符串引用
[0x00401000]> iz~ritual
[0x00401000]> iz~novruz
```

**Step 6：提取关键常量**
```bash
# 查看 stageFire 中的立即数
[0x00401000]> s main.stageFire
[0x0049bc20]> pd 40
# 逐条指令查看，记录 CMP 指令中的比较值

# 查看 rodata 中的分隔符
[0x00401000]> px 1 @0x4bf479
# 输出: 0x2d = '-'
```

**Step 7：使用 Radare2 的反编译功能（可选）**
```bash
# 如果安装了 r2ghidra 插件
[0x00401000]> pdg @main.stageFire
# 显示类似 Ghidra 的伪代码输出
```

**优势**：无需 GUI，SSH 到服务器也能用；`afl~main.` 一条命令找到所有目标函数；比手动解码字节码快得多。

---

### 3. Angr — 符号执行自动求解（一键出 Flag）

[Angr](https://github.com/angr/angr) 是 Python 符号执行框架，可以**自动求解约束条件**，无需手动列方程。

**安装：**
```bash
pip install angr
```

**详细操作步骤：**

**方法 A：基于成功/失败地址的符号执行**

需要先用 Ghidra/Radare2 找到关键地址：
- 成功路径：打印 `The ritual is complete.` 的地址
- 失败路径：打印各种失败消息的地址

```python
import angr
import claripy

# Step 1: 加载二进制
proj = angr.Project('./ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin', auto_load_libs=False)

# Step 2: 创建符号化输入
# 输入格式: "xxxx-xxxx-xxxx" (14个字符 + 换行符)
input_len = 15  # 14 chars + newline
sym_input = claripy.BVS('input', input_len * 8)

# Step 3: 设置初始状态
state = proj.factory.entry_state(stdin=angr.SimFile('/dev/stdin', content=sym_input))

# Step 4: 约束输入为可打印 ASCII
for i in range(14):
    state.solver.add(sym_input.get_byte(i) >= 0x20)
    state.solver.add(sym_input.get_byte(i) <= 0x7e)
# 分隔符位置固定为 '-'
state.solver.add(sym_input.get_byte(4) == ord('-'))
state.solver.add(sym_input.get_byte(9) == ord('-'))
# 换行符
state.solver.add(sym_input.get_byte(14) == ord('\n'))

# Step 5: 创建模拟管理器并探索
simgr = proj.factory.simulation_manager(state)

# 成功地址: 打印 "The ritual is complete." 的位置
# 失败地址: 打印 "Fire refused" / "Water rejected" / "Wind scattered" 的位置
# （这些地址需要从 Radare2/Ghidra 中获取）
FIND_ADDR = 0x49b9xx   # "ritual is complete" 的地址（需替换为实际值）
AVOID_ADDRS = [
    0x49bbxx,  # "Fire refused to burn."
    0x49bbxx,  # "Water rejected your offering."
    0x49bcxx,  # "Wind scattered the ashes."
]

simgr.explore(find=FIND_ADDR, avoid=AVOID_ADDRS)

# Step 6: 获取结果
if simgr.found:
    found_state = simgr.found[0]
    solution = found_state.solver.eval(sym_input, cast_to=bytes)
    phrase = solution[:14].decode()
    print(f"Phrase: {phrase}")
    print(f"Flag: novruzCTF{{{phrase}}}")
else:
    print("No solution found")
```

**方法 B：基于字符串匹配的符号执行（更简单）**

```python
import angr

proj = angr.Project('./ad1c72b0-ca4c-4899-8e24-962d6cbc60a9.bin', auto_load_libs=False)
state = proj.factory.entry_state()
simgr = proj.factory.simulation_manager(state)

# 直接搜索包含成功字符串的路径
def is_success(state):
    output = state.posix.dumps(1)  # stdout
    return b"ritual is complete" in output

def is_failure(state):
    output = state.posix.dumps(1)
    return (b"refused" in output or
            b"rejected" in output or
            b"scattered" in output or
            b"wrong" in output)

simgr.explore(find=is_success, avoid=is_failure)

if simgr.found:
    solution = simgr.found[0].posix.dumps(0)  # stdin
    print(f"Input: {solution}")
```

**注意事项：**
- Go 静态链接二进制体积大（~1.5MB 代码段），Angr 分析可能较慢（5-30 分钟）
- 如果整体符号执行太慢，可以只对单个 stage 函数做符号执行（Hook `main.main`，从特定地址开始）
- 方法 B 更简单但可能因 Go 运行时复杂性导致路径爆炸

**优势**：完全自动化，无需理解汇编或手动列方程；适合约束条件复杂、手动求解困难的题目。

---

### 4. IDA Free — 工业级反编译器

[IDA Free](https://hex-rays.com/ida-free/) 是 Hex-Rays 提供的免费版本，支持 x86-64 反编译。

**详细操作步骤：**

**Step 1：加载二进制**
1. 打开 IDA Free → 选择 "New" → 加载 bin 文件
2. 选择处理器类型 "MetaPC (x86-64)"
3. 等待自动分析完成

**Step 2：恢复 Go 符号**
- IDA Free 可能不会自动解析 Go pclntab
- 安装 [IDAGolangHelper](https://github.com/sibears/IDAGolangHelper) 插件：
  1. 下载插件放到 IDA 的 `plugins/` 目录
  2. Edit → Plugins → IDAGolangHelper → 选择 "Rename functions"
  3. 所有 Go 函数名被自动恢复

**Step 3：查看反编译结果**
1. 在 Functions 窗口搜索 `main_stageFire`
2. 按 F5 查看伪代码（IDA Free 8.x 已支持免费反编译）
3. 直接从伪代码中提取约束条件

**Step 4：交叉引用分析**
1. 在字符串窗口（Shift+F12）搜索 `novruzCTF{`
2. 双击跳转到字符串位置 → 按 X 查看交叉引用
3. 直接定位到 `main.main` 中的前缀校验代码

**优势**：反编译质量高，UI 交互体验好，适合详细分析复杂函数。

---

### 工具对比总结

| 工具 | 适用场景 | 本题耗时 | 优点 | 缺点 |
|------|---------|---------|------|------|
| **Ghidra** | 首选，通用逆向 | ~10 分钟 | 免费、反编译质量高、Go 支持好 | 需要 GUI、启动较慢 |
| **Radare2** | 快速分析、无 GUI 环境 | ~15 分钟 | CLI、轻量、SSH 可用 | 学习曲线陡峭 |
| **Angr** | 自动求解约束 | ~5-30 分钟 | 全自动、无需手动分析 | Go 二进制可能较慢 |
| **IDA Free** | 深度分析 | ~10 分钟 | 反编译质量最高 | 仅限非商业用途 |
| **手动反汇编** | 无工具环境 | ~2 小时 | 不依赖任何工具 | 极其耗时、容易出错 |

**推荐流程**：Ghidra 加载 → 反编译 3 个 stage 函数 → 提取约束 → Python 求解 → 5-10 分钟内完成。如果约束复杂也可以用 Angr 自动求解。
