---
title: Web 新手上手操作指南
---

# Web 新手上手操作指南

Web 题的第一步不是马上扫目录或丢 payload，而是搞清楚页面、接口、参数、鉴权和状态分别在哪里。新手最重要的是建立“浏览器看到的内容”和“真实请求响应”之间的关系。

## 这类题先看什么

先确认：

1. 入口是单页面、登录系统、API、下载功能还是管理后台？
2. 页面源码、JS、Cookie、LocalStorage、响应头里有没有线索？
3. 哪些参数可控？GET、POST、JSON、Header、Cookie、路径片段？
4. 成功条件是什么？返回 flag、进入 admin、读文件、触发命令还是绕过鉴权？

## 最小工具集

| 工具 | 用途 |
|------|------|
| 浏览器 DevTools | 看 DOM、源码、网络请求、存储状态 |
| Burp Suite | 重放请求、改参数、观察响应差异 |
| `curl` | 最小化复现请求，便于写脚本 |
| `ffuf` / dirsearch | 有线索时枚举路径或参数 |
| Python | 自动化请求、盲注、批量尝试 |

## 首轮 10 分钟操作流程

### Step 1：先看页面本身

- 查看页面文本、隐藏元素、注释。
- 打开 DevTools 的 Network，刷新页面。
- 看请求路径、状态码、响应头、Cookie、LocalStorage。
- 查看 JS 是否写死接口、路径、角色字段或 flag 片段。

### Step 2：用 Burp 或 curl 复现请求

把关键请求复制成 `curl`，确认你能在命令行复现页面行为：

```bash
curl -i 'https://example.invalid/path?name=test'
```

能复现后，再尝试：

- 改参数值
- 改 Cookie / Header
- 改路径大小写或后缀
- 改 JSON 字段类型

### Step 3：先做低噪声枚举

只有在页面或响应里出现线索时，再做枚举。例如：

- `robots.txt`、`sitemap.xml`
- JS 里出现 `/api/`、`/admin`、`/debug`
- 报错泄漏框架、模板引擎或文件路径

### Step 4：按漏洞信号分流

| 信号 | 可能方向 |
|------|----------|
| 参数像文件名 | 文件读取 / 路径穿越 |
| 页面渲染了输入 | XSS / SSTI |
| SQL 报错或过滤关键字 | SQLi / WAF 绕过 |
| URL 参数是内网地址 | SSRF |
| Cookie 存角色或状态 | 客户端状态篡改 |
| 上传/下载功能 | 文件解析、路径、类型绕过 |

## 典型突破口

- 源码注释和 JS 里的隐藏路由。
- Cookie / LocalStorage 中可篡改的身份或状态。
- 接口返回的调试字段、错误栈、路径信息。
- 文件读取参数：`file`、`path`、`page`、`template`、`url`。
- 过滤器不完整导致的 WAF 绕过。
- 前端限制严，后端校验弱。

## 新手常见误区

- 只看页面，不看 Network 里的真实请求。
- 上来就大规模扫目录，忽略页面源码里已经给出的路径。
- 只在浏览器里点，不把请求复制成可复现的 `curl`。
- 看到过滤就放弃，没有先确认过滤发生在前端还是后端。
- 没记录每次参数变化导致的响应差异。

## 仓库内参考阅读

- [CPCTF mirage](../Web/CPCTF_mirage.md) — 先跳出视觉层，看源码与页面真实内容。
- [You may have the Flag](../Web/kashiCTF_You_may_have_the_Flag.md) — Web 工具对比和请求复现流程。
- [Python Server](../Web/NovruzCTF_python-serverl.md) — 文件读取 / 路径类题目的操作路线。
- [Lorem Ipsum Arcanum Invocatum payload FAQ](../Web/putcCTF_Lorem_Ipsum_Arcanum_Invocatum_payload_faq.md) — 复杂 payload 拆解方式。

## 一页式检查清单

- [ ] 看过页面源码、注释和 JS
- [ ] 看过 Network 中的所有关键请求
- [ ] 复制出至少一个可复现的 `curl`
- [ ] 检查过 Cookie、LocalStorage、Session 相关字段
- [ ] 找出所有可控参数：URL、Body、Header、Cookie、路径
- [ ] 根据响应差异判断了可能漏洞方向
- [ ] 只在有线索时进行目录或参数枚举
- [ ] 把最终利用步骤整理成可重复请求