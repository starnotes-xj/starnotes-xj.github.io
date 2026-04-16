# MetaCTF - Physics Notes Writeup

## 题目信息
- **比赛**: MetaCTF
- **题目**: Physics Notes
- **类别**: Crypto
- **难度**: 简单
- **附件/URL**: `notes.txt`（根据题目附件内容整理）
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Physics%20Notes/notes.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Physics%20Notes){target="_blank"}
- **Flag格式**: `DawgCTF{...}`
- **状态**: 已解

## Flag

```text
DawgCTF{therm0dyn4mic5sucks!}
```

## 解题过程

### 1. 初始侦察/文件识别
- 附件是一大段看似正常的热力学/理想气体学习笔记，表面上没有明显的加密参数、密文块或编码串。
- 先按题意优先尝试 `security-hub` MCP：
  - `ctf_detect` 把内容误判成了 `solfege` / `rsa_generic`
  - `ctf_solve` 也没有直接恢复出 Flag
- 这说明它并不是一道标准的 RSA、古典密码或多层编码题，更像是**藏在文本结构中的信息提取题**。

### 2. 关键突破点一
- 仔细观察文本可以发现：
  - 每一行的**首字符**和**末字符**都比较“刻意”
  - 前几行的首尾字符拼起来很像 Flag 头
- 对前几行尝试“**每行取首字符和末字符**”：

| 行号 | 首字符 | 末字符 | 提取结果 |
|------|--------|--------|----------|
| 1 | `D` | `a` | `Da` |
| 2 | `w` | `g` | `wg` |
| 3 | `C` | `T` | `CT` |
| 4 | `F` | `{` | `F{` |

- 直接拼接可得：

```text
DawgCTF{
```

- 到这里基本可以确认，隐藏方式就是**按行抽取首尾字符**。

### 3. 关键突破点二
- 对前 14 行继续执行同样的规则：`line[0] + line[-1]`
- 第 15 行内容为：

```text
}]\d\wa\dT
```

- 这一行如果继续取首尾字符会得到 `}T`，明显多出一个无关字符。
- 因此前 14 行取“首+尾”，第 15 行只取**首字符 `}`** 作为闭合符号。

完整提取结果如下：

| 行号 | 提取 |
|------|------|
| 1 | `Da` |
| 2 | `wg` |
| 3 | `CT` |
| 4 | `F{` |
| 5 | `th` |
| 6 | `er` |
| 7 | `m0` |
| 8 | `dy` |
| 9 | `n4` |
| 10 | `mi` |
| 11 | `c5` |
| 12 | `su` |
| 13 | `ck` |
| 14 | `s!` |
| 15 | `}` |

拼接得到：

```text
DawgCTF{therm0dyn4mic5sucks!}
```

### 4. 获取 Flag
- 最终隐藏信息即为：

```text
DawgCTF{therm0dyn4mic5sucks!}
```

## 攻击链/解题流程总结

```text
阅读伪装成物理笔记的文本 → 先尝试 security-hub 自动检测/自动求解 → 发现不是标准密码题 → 观察每行首尾字符 → 前 14 行取“首+尾”、第 15 行取“首” → 拼接得到 Flag
```

## 漏洞分析 / 机制分析

### 根因
- 本题并非传统密码学漏洞，而是**文本隐写 / 结构化藏字**。
- 出题者利用大量正常的物理公式作为掩护，将真正信息埋入每一行的边界字符中。

### 影响
- 如果只盯着公式内容本身，会被误导去分析热力学符号、正则片段、幂运算或伪 RSA 线索。
- 一旦识别出“按行取边界字符”的模式，Flag 可以在极短时间内恢复。

### 修复建议（适用于漏洞类题目）
- 本题为 CTF 题目，不涉及真实系统漏洞修复。
- 若在真实场景中需要检测类似隐写，应增加：
  - 按行首尾字符统计
  - 可疑文本结构分析
  - 自动化 acrostic / telestich / 边界字符提取检查

## 知识点
- 文本隐写（Text Steganography）
- Acrostic / Telestich / 边界字符提取
- 自动化工具误判后的人工结构分析

## 使用的工具
- Security Hub MCP — `ctf_detect` / `ctf_solve` 用于快速排除常规密码学题型
- Python — 本地验证首尾字符提取逻辑

## 脚本归档
- Go：[`MetaCTF_Physics_Notes.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/MetaCTF_Physics_Notes.go){target="_blank"}
- Python：[`MetaCTF_Physics_Notes.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/MetaCTF_Physics_Notes.py){target="_blank"}
- 说明：脚本用于复现首尾字符提取过程

## 命令行提取关键数据（无 GUI）

```bash
# Python 版本复现
python CTF_Writeups/scripts_python/MetaCTF_Physics_Notes.py

# Go 版本复现
go run CTF_Writeups/scripts_go/MetaCTF_Physics_Notes.go
```

## 推荐工具与优化解题流程

> 这类题不一定真的是“密码算法题”，有时更接近文本隐写与模式识别。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Security Hub MCP | 初筛 | 秒级 | 能快速排除常见密码学方向 | 面对文本隐写容易误判 |
| 手工观察 | 模式发现 | 分钟级 | 对结构异常非常敏感 | 依赖经验 |
| Python/Go 脚本 | 结果复现 | 秒级 | 可验证、可归档 | 需要先发现规律 |

### 推荐流程

**推荐流程**：先用 MCP 快速判断是否为常规密码题 → 若无结果则检查行结构、首字母、尾字母、特殊符号分布 → 写一个最小脚本复现 → 输出 Flag。

### 工具 A（推荐首选）
- **安装**：启用 `security-hub` MCP
- **详细步骤**：
  1. 使用 `ctf_detect` 判断是否为 RSA / 古典密码 / 编码类题
  2. 若输出和题面特征明显不匹配，则转向人工结构分析
  3. 检查首字母、末字母、标点、固定列等文本隐写特征
- **优势**：能先快速缩小搜索范围

### 工具 B（可选）
- **安装**：Python 3 或 Go 1.20+
- **详细步骤**：
  1. 将文本按行切分
  2. 对前 14 行提取首尾字符
  3. 对第 15 行仅取首字符并拼接
- **优势**：复现简单，便于写入仓库长期保存
