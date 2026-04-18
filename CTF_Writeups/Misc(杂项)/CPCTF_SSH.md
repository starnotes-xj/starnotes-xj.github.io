# CPCTF - SSH Writeup

## 题目信息
- **比赛**: CPCTF
- **题目**: SSH
- **类别**: Shell / Misc
- **难度**: 简单
- **附件/URL**: `ssh ssh@133.88.122.244 -p 32437`
- **附件链接**: [下载 service_info.txt](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/SSH/service_info.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/SSH){target="_blank"}
- **Flag格式**: `CPCTF{...}`
- **状态**: 已解

## Flag

```text
CPCTF{w31c0m3_2_c11_w0r1d}
```

## 解题过程

### 1. 初始侦察 / 连接服务
- 题目本身已经把关键信息给得非常直白：
  - 连接方式：`ssh ssh@133.88.122.244 -p 32437`
  - 密码：`cpctf2026`
  - flag 位置：`/flag/flag.txt`

- 因此第一步就是直接连上去：

```bash
ssh ssh@133.88.122.244 -p 32437
```

- 输入密码后，会进入一个普通的 Linux shell 环境，题面也给了类似这样的提示：

```text
ssh2@shell-ssh-jwefairt-6f75f5cdb6-hb425:~$
```

- 题目提示本质上是在教选手使用 Linux 基础命令：
  - `ls`：列出目录内容
  - `cat <文件路径>`：显示文件内容
  - `man <命令>`：查看手册
  - `compgen -c`：查看可用命令列表

### 2. 关键突破点
- 这题没有绕弯，也没有做额外限制。
- 既然题面已经明确说明 flag 在 `/flag/flag.txt`，最直接的做法就是先进入对应目录，再查看文件内容。

- 我采用的是下面这组命令：

```bash
cd /flag
ls
cat flag.txt
```

- 其中：
  - `cd /flag` 进入题目提示给出的目录
  - `ls` 确认目录下确实存在 `flag.txt`
  - `cat flag.txt` 直接输出文件内容

### 3. 获取 Flag
- 执行完上面的命令后，终端直接回显：

```text
CPCTF{w31c0m3_2_c11_w0r1d}
```

## 攻击链 / 解题流程总结

```text
使用给定 SSH 凭据登录 -> 进入 /flag 目录 -> 用 ls 确认文件存在 -> 用 cat 读取 flag.txt -> 获得 flag
```

## 机制分析

### 本题考点
- 这题本质上不是漏洞利用，而是一个 **Linux / shell 入门题**。
- 核心目标是让选手学会：
  - 用 SSH 登录远端环境
  - 用基础命令在文件系统中移动与查看文件

### 为什么能直接解
- 题目已经把最关键的信息全部告诉了选手：
  - 登录方式
  - 密码
  - flag 所在路径
- 所以真正要做的事情只有两步：
  1. 成功登录
  2. 正确使用 `cd`、`ls`、`cat`

### 影响 / 对应真实场景
- 在真实系统里，如果攻击者已经拿到了 SSH 口令并能登录 shell，那么后续最基本的能力就是：
  - 浏览目录
  - 查看敏感文件
  - 收集环境信息
- 这题用的是最温和的教学版本，只要求选手读取固定路径下的 flag 文件。

## 知识点
- SSH 基本连接方式
- Linux 目录切换：`cd`
- 文件枚举：`ls`
- 文件查看：`cat`
- 命令帮助：`man`

## 使用的工具
- OpenSSH 客户端 — 连接远端题目环境
- Linux shell 基础命令（`cd` / `ls` / `cat`）— 定位并读取 flag

## 脚本归档
- 本题无需额外脚本
- 说明：解题过程完全由交互式 shell 命令完成，重点在基础命令使用

## 命令行提取关键数据（无 GUI）

```bash
# 连接远端
ssh ssh@133.88.122.244 -p 32437

# 登录后输入密码
cpctf2026

# 进入目标目录并读取 flag
cd /flag
ls
cat flag.txt
```

## 推荐工具与优化解题流程

> 这题不是“复杂利用”，而是“最短路径拿到 shell 中的目标文件”。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| OpenSSH | 登录与交互 | 秒级 | 系统通常自带，最直接 | 需要手动输入密码 |
| Paramiko / 脚本化 SSH | 自动化验证 | 秒级 | 适合批量验证与归档 | 对这题来说有点过度 |
| `man` / `compgen -c` | 命令学习 | 视情况而定 | 适合不熟 Linux 的选手 | 本题不需要深入使用 |

### 推荐流程

**推荐流程**：先用 SSH 登录 -> 根据题面进入 `/flag` -> `ls` 看目录 -> `cat flag.txt` 直接读取内容。

### 工具 A（推荐首选）
- **安装**：系统自带 OpenSSH 客户端
- **详细步骤**：
  1. 执行 `ssh ssh@133.88.122.244 -p 32437`
  2. 输入密码 `cpctf2026`
  3. 执行 `cd /flag && ls && cat flag.txt`
- **优势**：最符合题目设计，完全不需要额外环境

### 工具 B（可选）
- **安装**：Python 3 + `paramiko`
- **详细步骤**：
  1. 用脚本连接远端 SSH
  2. 远程执行 `cat /flag/flag.txt`
  3. 打印输出
- **优势**：适合做归档验证，但不如直接交互来得直观
