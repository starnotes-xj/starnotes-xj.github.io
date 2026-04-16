# Hack For A Change 2026 March (UN SDG3) - GenomeRand Clinical Randomization System Writeup

## 题目信息
- **比赛**: Hack For A Change 2026 March (UN SDG3)
- **题目**: GenomeRand Clinical Randomization System
- **类别**: 密码学
- **难度**: Easy
- **附件/URL**: 题目描述与输出（无额外附件）
- **附件链接**: 无
- **Flag格式**: SDG{}
- **状态**: 已解

## Flag

```text
SDG{11482}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点：题目描述直接给出 LCG 参数与输出定义
- 关键线索：输出为 `state >>> 16`（仅高 16 位）

### 2. 关键突破点一
- 递推关系：

$$\text{state}_{n+1} = (a\cdot\text{state}_n + c) \bmod 2^{32}$$

- 输出关系：

$$\text{output}_n = \text{state}_n \gg 16$$

- 已知连续输出：

```text
[52338, 24512, 16929, 35379]
```

### 3. 关键突破点二
- 对 $\text{state}_0$ 低 16 位做 $2^{16}$ 枚举：

$$\text{state}_0 = (\text{output}_0 \ll 16) \;|\; \text{low}_{16}$$

- 逐步验证 $\text{output}_1, \text{output}_2, \text{output}_3$，唯一解：

```text
state0 = 3430075636 (0xcc72ccf4)
```

### 4. 获取 Flag
- 从 $\text{state}_0$ 迭代 100 次，得到：

```text
output_100 = 11482
```

## 攻击链/解题流程总结

```text
识别 LCG → 枚举低 16 位 → 连续输出校验 → 推进到位置 100 → 得出输出
```

## 漏洞分析 / 机制分析

### 根因
- 输出暴露了内部状态的高 16 位，且 LCG 为线性递推，低 16 位可被枚举并用连续输出验证。

### 影响
- 可恢复完整状态并预测任意未来输出。

### 修复建议（适用于漏洞类题目）
- 使用 CSPRNG（如 AES-CTR/ChaCha20）代替 LCG。
- 不暴露连续输出，或只暴露经过不可逆混淆/哈希后的值。

## 知识点
- 线性同余生成器（LCG）
- 状态泄露与预测攻击
- 低位枚举 + 连续输出校验

## 使用的工具
- Python 3 — 枚举低 16 位并推进状态
- Go 1.20+ — 同步实现验证

## 脚本归档
- Go：[`HackForAChange2026March_UN_SDG3_GenomeRand_LCG.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/HackForAChange2026March_UN_SDG3_GenomeRand_LCG.go){target="_blank"}
- Python：[`GenomeRand_LCG.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/GenomeRand_LCG.py){target="_blank"}
- 说明：解题代码需包含详细注释（本题脚本已补充注释）。

## 命令行提取关键数据（无 GUI）

```bash
python3 CTF_Writeups/scripts_python/HackForAChange2026March_UN_SDG3_GenomeRand_LCG.py
# 或
# go run CTF_Writeups/scripts_go/HackForAChange2026March_UN_SDG3_GenomeRand_LCG.go
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
| --- | --- | --- | --- | --- |
| Python 脚本 | 枚举+验证 | N/A | 自动化、可复现 | 需写代码 |
| Go 脚本 | 枚举+验证 | N/A | 类型安全、易集成 | 需编译/运行环境 |
| 手算 | 理解原理 | N/A | 直观 | 易出错 |

### 推荐流程

**推荐流程**：手动理解参数 → Python/Go 枚举验证 → 输出预测值。

### 工具 A（推荐首选）
- **安装**：Python 3
- **详细步骤**：
  1. 填入已知输出序列
  2. 枚举低 16 位并验证连续输出
  3. 推进到位置 100 输出结果
- **优势**：稳定、易复用

### 工具 B（可选）
- **安装**：Go 1.20+
- **详细步骤**：
  1. 运行 Go 脚本完成枚举
  2. 输出 position 100 的结果
- **优势**：类型安全，便于集成到工具链
