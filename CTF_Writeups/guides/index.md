---
title: 新手上手指南
---

# 新手上手指南

这组文档面向刚开始做 CTF、拿到附件或题目页面时“不知道第一步看什么”的同学。目标不是替代具体 writeup，而是给每个方向一套固定起手流程：先做低成本侦察，再决定是否上重工具、写脚本或深入分析。

## 怎么使用这套指南

1. 先根据题目分类选择对应方向。
2. 按“首轮 10 分钟操作流程”做第一轮侦察。
3. 根据“典型突破口”决定下一步路线。
4. 卡住时回到“一页式检查清单”，确认有没有漏掉最便宜的线索。
5. 最后再去读仓库里的参考 writeup，看完整题目如何落地。

## 方向入口

<div class="grid cards" markdown>

-   :material-web:{ .lg .middle } __Web__

    ---

    从页面、源码、接口、参数、鉴权和请求响应开始建立侦察习惯。

    [:octicons-arrow-right-24: Web 新手指南](web.md)

-   :material-lock:{ .lg .middle } __Crypto__

    ---

    先识别题型，再分流到编码、古典密码、RSA、PRNG、对称加密或实现漏洞。

    [:octicons-arrow-right-24: Crypto 新手指南](crypto.md)

-   :material-cog-refresh:{ .lg .middle } __Reverse__

    ---

    从 `file` / `strings` 到 Ghidra 最小操作流，解决“拿到附件没思路”的问题。

    [:octicons-arrow-right-24: Reverse 新手指南](reverse.md)

-   :material-puzzle:{ .lg .middle } __Misc__

    ---

    先判定文件、容器、元数据和隐藏内容，再选择对应工具链。

    [:octicons-arrow-right-24: Misc 新手指南](misc.md)

-   :material-code-braces:{ .lg .middle } __PPC__

    ---

    先读输入输出格式与约束，再判断暴力、数学化、模拟或搜索。

    [:octicons-arrow-right-24: PPC 新手指南](ppc.md)

-   :material-bug:{ .lg .middle } __Pwn__

    ---

    从文件识别、保护检查、基础交互和最短利用链开始。

    [:octicons-arrow-right-24: Pwn 新手指南](pwn.md)

</div>

## 共通原则

### 1. 先做最低成本侦察

不要一上来就开最复杂的工具。多数题第一轮都应该先确认：

- 题目给了什么入口：网页、附件、服务、脚本、源码、二进制、数据文件
- 有没有显眼字符串、注释、报错、文件类型、压缩层或元数据
- 输入来自哪里：URL 参数、表单、stdin、argv、环境变量、文件、网络
- 成功条件是什么：打印 flag、跳到成功页、通过校验、生成文件、返回特定响应

### 2. 先判断题型，再选工具

工具不是越强越好，而是要匹配题目阶段：

| 阶段 | 目标 | 常见工具 |
|------|------|----------|
| 初筛 | 判断类型和入口 | `file`、`strings`、浏览器、文本编辑器 |
| 定位 | 找关键函数、接口、参数、数据 | Ghidra、Burp、DevTools、Python |
| 验证 | 证明猜想正确 | 小脚本、curl、gdb、pwntools |
| 自动化 | 稳定复现结果 | Python / Go 脚本、批量请求、求解器 |

### 3. 每一步都记录中间结论

CTF 题目常常不是一步到位。建议每一步都写一句短结论：

```text
输入来源是什么？
程序/服务拿输入做了什么？
我现在能控制什么？
下一步要验证什么？
```

这些记录最后也能直接转成 writeup。

## 写 writeup 时怎么衔接

写题解时仍然以 [`WRITEUP_TEMPLATE.md`](../WRITEUP_TEMPLATE.md) 为准。新手指南只解决“做题时怎么起步”，正式归档还要检查：

- writeup 是否放入正确分类目录
- 附件是否放入 `CTF_Writeups/files/`
- 脚本是否放入 `scripts_python/` 或 `scripts_go/`
- 分类索引页与比赛索引页是否更新
- 附件链接、脚本链接是否可访问