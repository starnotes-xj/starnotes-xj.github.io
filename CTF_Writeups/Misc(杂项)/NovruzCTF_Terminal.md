# NovruzCTF - Terminal Writeup

## 题目信息
- **比赛**: NovruzCTF
- **题目**: Terminal
- **类别**: Misc
- **难度**: Medium
- **附件/URL**: `nc 95.111.234.103 9999`
- **Flag格式**: novruzCTF{}
- **状态**: 已解

## Flag

```text
novruzctf{H1DD3N_F1L3S_4R3_N0T_S4F3_FR0M_Y0U}
```

## 解题过程

### 1. 初始侦察

连接后进入一个受限 shell 环境，以 guest 身份登录，需要提权到 root 才能获取 flag。

```text
guest@ghost-server:/$ help
Commands:
 ls [-a]   : List files (use -a to see hidden)
 cd <dir>  : Change directory
 cat <file>: Read file
 pwd       : Show path
 auth <pwd>: Elevate to Root
 getflag   : Retrieve Flag (Root Only)
 exit      : Disconnect
```

关键命令：`auth <pwd>` 可以提权，`getflag` 需要 root 权限。目标是找到密码。

### 2. 文件系统探索

```text
guest@ghost-server:/$ ls
var/  home/  readme.txt

guest@ghost-server:/$ cat readme.txt
SECURITY NOTICE:
We detected an intrusion.
All admin credentials have been moved to the backup folder in '/var/backups'.
Find them and secure the system.
```

线索指向 `/var/backups` 目录。

### 3. 发现隐藏文件

进入备份目录，常规 `ls` 只显示一个日志文件：

```text
guest@ghost-server:/var/backups$ ls
sys_restore.log

guest@ghost-server:/var/backups$ cat sys_restore.log
[INFO] Backup started.
[INFO] Compressing data...
[WARN] .integrity_check file created (HIDDEN).
```

日志提示存在隐藏的 `.integrity_check` 文件。使用 `ls -a` 查看：

```text
guest@ghost-server:/var/backups$ ls -a
sys_restore.log  .integrity_check

guest@ghost-server:/var/backups$ cat .integrity_check
FAIL: Hash mismatch.
SAVED_CREDENTIAL_DUMP: q#9L!z@X_v2$mR
```

获得凭证：`q#9L!z@X_v2$mR`

### 4. 提权并获取 Flag

```text
guest@ghost-server:/var/backups$ auth q#9L!z@X_v2$mR
[+] AUTHENTICATION SUCCESSFUL.
[+] WELCOME, ADMINISTRATOR.

root@ghost-server:/var/backups$ getflag
[***] SYSTEM UNLOCKED [***]
novruzctf{H1DD3N_F1L3S_4R3_N0T_S4F3_FR0M_Y0U}
```

## 攻击链/解题流程总结

```text
cat readme.txt(线索指向/var/backups) → cat sys_restore.log(提示隐藏文件) → ls -a(发现.integrity_check) → cat .integrity_check(获取凭证) → auth提权 → getflag
```

## 漏洞分析 / 机制分析

### 根因
管理员将凭证明文存储在隐藏文件中，依赖"隐藏=安全"的错误假设。Linux 隐藏文件（以 `.` 开头）仅是不在默认 `ls` 输出中显示，不提供任何访问控制。

### 影响
- 任何有文件读取权限的用户都可以获取 root 凭证
- 完全的权限提升

### 修复建议
1. 不要将凭证以明文形式存储在文件系统中
2. 使用密钥管理系统（如 HashiCorp Vault）存储敏感凭证
3. 对备份目录设置严格的文件权限（`chmod 700`）
4. 隐藏文件不等于安全，需要 ACL 或加密保护

## 知识点
- Linux 隐藏文件机制（`.` 前缀，`ls -a` 查看）
- 受限 shell 环境的信息收集思路
- 日志文件中可能泄露敏感信息的线索
- "Security through obscurity" 的局限性

## 使用的工具
- netcat (`nc`) — 连接远程服务
- 内置 shell 命令 (`ls -a`, `cat`, `cd`) — 文件系统探索

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_terminal.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_terminal.py`

## 命令行提取关键数据（无 GUI）

```bash
# 一键自动化解题（expect 脚本风格）
{ echo "cd var/backups"; echo "cat .integrity_check"; sleep 1; echo "auth q#9L!z@X_v2\$mR"; sleep 1; echo "getflag"; } | nc 95.111.234.103 9999
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| 手动 nc 交互 | 全流程 | ~2 min | 直观，适合探索 | 无法自动化 |
| pwntools | 自动化交互 | ~1 min | 可编程、可重复 | 需要写脚本 |
| expect | 自动化交互 | ~1 min | 轻量 | 语法不够灵活 |

### 推荐流程

**推荐流程**：nc 手动探索 → 发现线索链 → 提权获取 flag（预估 2-3 分钟）。

### 手动 nc 交互（推荐）
- **安装**：系统自带
- **详细步骤**：
  1. 连接服务，`ls` + `cat readme.txt` 获取初始线索
  2. 进入 `/var/backups`，查看日志发现隐藏文件提示
  3. `ls -a` 找到隐藏文件，读取凭证
  4. `auth` 提权后 `getflag`
- **优势**：本题交互量小，手动最快

### pwntools 自动化（可选）
- **安装**：`pip install pwntools`
- **详细步骤**：见脚本归档
- **优势**：批量测试、自动化复现
