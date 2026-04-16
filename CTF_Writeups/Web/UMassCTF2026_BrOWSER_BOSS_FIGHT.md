# UMassCTF 2026 - BrOWSER BOSS FIGHT Writeup

## 题目信息
- **比赛**: UMassCTF 2026
- **题目**: BrOWSER BOSS FIGHT
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `http://browser-boss-fight.web.ctf.umasscybersec.org:32770/`
- **附件链接**: 无附件，题目为在线靶机
- **Flag格式**: `UMASS{...}`
- **状态**: 已解

## Flag

```text
UMASS{br0k3n_1n_2_b0wz3r5_c4st13}
```

## 解题过程

### 1. 初始侦察 / 文件识别
- 入口点只有一个首页：

```text
http://browser-boss-fight.web.ctf.umasscybersec.org:32770/
```

- 先按题意优先使用 `security-hub` 的 `web_fingerprint` 做快速识别，确认站点是 `Express / Node.js`，没有明显的现成 CMS 或框架后台。
- 继续直接查看首页源码，能看到一个非常关键的前端逻辑：

```html
<script>
    document.getElementById('key-form').onsubmit = function() {
        const knockOnDoor = document.getElementById('key');
        knockOnDoor.value = "WEAK_NON_KOOPA_KNOCK";
        return true;
    };
</script>
```

- 这说明正常在浏览器里输入任何 key，提交时都会被前端强制改成 `WEAK_NON_KOOPA_KNOCK`。
- 因此第一结论已经很明确：**不能按正常前端流程交互，必须自己发 HTTP 请求**。

### 2. 关键突破点一
- 接下来继续观察首页响应头，发现 `Server` 头里直接留了提示：

```text
BrOWSERS CASTLE (A note outside: "King Koopa, if you forget the key, check under_the_doormat! - Sincerely, your faithful servant, Kamek")
```

- 这里的 `under_the_doormat` 就是正确 key。
- 因此直接绕过前端，手工提交：

```http
POST /password-attempt
key=under_the_doormat
```

- 这一步不会直接返回 flag，而是返回一个重定向：

```http
HTTP/1.1 302 Found
Location: /bowsers_castle.html
Set-Cookie: connect.sid=...
```

- 也就是说第一阶段只是“进门”，真正的 Bowser 判定发生在第二阶段的：

```text
/bowsers_castle.html
```

### 3. 关键突破点二
- 访问 `/bowsers_castle.html` 时，服务端会设置一大串 Cookie，最后还有一个非常关键的状态位：

```text
hasAxe=false
```

- 页面内容也对应这条状态：

```html
<p class="bowser-speech">I don't know how you got in, but you can't possibly defeat me! I removed the axe!</p>
```

- 这题真正的核心并不是找新接口，也不是 XSS，而是**浏览器端状态信任**。
- 只要在访问 `/bowsers_castle.html` 时，把请求里的 Cookie 改成：

```http
Cookie: connect.sid=...; hasAxe=true
```

- 服务端就会直接返回胜利页：

```html
<body class="victory-body">
    <p class="victory-text">UMASS{br0k3n_1n_2_b0wz3r5_c4st13}</p>
</body>
```

- 实测即使请求里同时出现：

```http
hasAxe=true; hasAxe=false
```

  依然能拿到胜利页，说明后端在解析重复 Cookie 时采用了“取第一个值”或等价逻辑。

### 4. 获取 Flag
- 最终利用链非常短：
  1. 绕过首页 JavaScript，手工提交 `key=under_the_doormat`
  2. 取回 `connect.sid`
  3. 请求 `/bowsers_castle.html`
  4. 手工加上 `hasAxe=true`

- 返回的胜利页中直接包含 flag：

```text
UMASS{br0k3n_1n_2_b0wz3r5_c4st13}
```

## 攻击链 / 解题流程总结

```text
security-hub 指纹识别 Express/Node.js -> 查看首页源码发现前端会强制改 key -> 从 Server 响应头获得提示 under_the_doormat -> 手工 POST /password-attempt -> 拿到 302 到 /bowsers_castle.html 和 connect.sid -> 在后续请求里伪造 hasAxe=true -> 进入 victory 页面得到 Flag
```

## 漏洞分析 / 机制分析

### 根因
- 站点把“是否拿到斧头”这种关键状态放在客户端可控的 Cookie `hasAxe` 中。
- 服务端直接信任这个 Cookie，而不是在服务端 session 或数据库中维护状态。
- 首页还试图用前端 JavaScript 阻止用户输入真实 key，但这类控制天然不具备安全性。

### 影响
- 攻击者可以完全绕过前端脚本，直接构造 HTTP 请求。
- 一旦发现关键状态字段 `hasAxe`，就可以通过篡改 Cookie 直接越过游戏逻辑，进入胜利分支。
- 这类问题在真实系统里会导致权限提升、流程绕过或业务状态伪造。

### 修复建议（适用于漏洞类题目）
- 不要把关键业务状态存放在客户端可修改 Cookie 中，至少应放在服务端 session 中维护。
- 如果必须把状态放到客户端，应进行完整性保护，例如带签名的 token，并在服务端验证。
- 前端 JavaScript 只能用于交互优化，不能承担安全校验职责。
- 对重定向后的关键页面应在服务端重新校验访问条件，而不是只读取某个裸 Cookie。

## 知识点
- 前端校验不可作为安全边界
- 客户端可控 Cookie 篡改
- 重定向链上的状态机分析
- 重复 Cookie 解析顺序对逻辑判断的影响

## 使用的工具
- **Security Hub MCP**: `web_fingerprint` 用于初始指纹识别，确认站点是 Express / Node.js
- **PowerShell / Invoke-WebRequest**: 直接重放请求、查看响应头、验证 302 跳转与 Cookie 逻辑
- **浏览器开发者工具 / 代理工具**: 观察页面源码和请求流程，手工篡改 Cookie

## 脚本归档
- Go：[`UMassCTF2026_BrOWSER_BOSS_FIGHT.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/UMassCTF2026_BrOWSER_BOSS_FIGHT.go){target="_blank"}
- Python：[`UMassCTF2026_BrOWSER_BOSS_FIGHT.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/UMassCTF2026_BrOWSER_BOSS_FIGHT.py){target="_blank"}
- 说明：两个脚本都会自动完成绕过前端、抓取 `connect.sid`、伪造 `hasAxe=true` 并提取 flag

## 命令行提取关键数据（无 GUI）

```bash
# 1. 查看首页源码，确认前端会强制替换 key
curl http://browser-boss-fight.web.ctf.umasscybersec.org:32770/

# 2. 观察响应头中的提示
curl -i http://browser-boss-fight.web.ctf.umasscybersec.org:32770/

# 3. 运行 Go 版复现脚本
go run CTF_Writeups/scripts_go/UMassCTF2026_BrOWSER_BOSS_FIGHT.go

# 4. 运行 Python 版复现脚本
python CTF_Writeups/scripts_python/UMassCTF2026_BrOWSER_BOSS_FIGHT.py
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Security Hub MCP** | 初始指纹识别 | 秒级 | 快速确认技术栈 | 更深层交互仍需手工验证 |
| **PowerShell / curl** | 重放与篡改请求 | 分钟级 | 对这题最直接，易复现 | 需要手工观察响应头和 Cookie |
| **Burp Suite** | 交互式篡改 Cookie | 分钟级 | 改 Cookie 最方便，适合演示 | 依赖 GUI |

### 推荐流程

**推荐流程**：先看首页源码确认是否只有前端拦截 -> 再看响应头找提示 -> 手工提交真实 key -> 跟踪 302 后的目标页面 -> 检查并篡改关键 Cookie -> 直接取 flag。

### 工具 A（推荐首选）
- **安装**: Python 3 或系统自带 PowerShell / curl
- **详细步骤**:
  1. 获取首页源码与响应头
  2. 手工 POST `key=under_the_doormat`
  3. 提取 `connect.sid` 和 `Location`
  4. 带 `hasAxe=true` 请求目标页面
- **优势**: 纯 HTTP 层复现，最贴合这题的本质

### 工具 B（可选）
- **安装**: Burp Suite
- **详细步骤**:
  1. 在浏览器中正常打开题目页面
  2. 用 Repeater 重发 `/password-attempt`
  3. 在 `/bowsers_castle.html` 请求中把 `hasAxe=false` 改成 `hasAxe=true`
  4. 查看胜利页中的 flag
- **优势**: 对 Cookie 篡改和重放链路可视化更强
