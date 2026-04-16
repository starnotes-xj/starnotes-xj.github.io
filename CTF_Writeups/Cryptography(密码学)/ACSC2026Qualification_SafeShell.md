# ACSC Qualification 2026 - SafeShell Writeup

!!! warning "发布提醒"
    官方 Qualification 页面显示本轮时间为 **2026-03-01 18:00 CEST ～ 2026-05-01 18:00 CEST**。当前文档适合作为**本地归档草稿**；若比赛尚未结束，请勿提前公开发布。

## 题目信息
- **比赛**: ACSC Qualification 2026（Austria Cyber Security Challenge 2026 Qualification）
- **题目**: SafeShell
- **类别**: Crypto
- **难度**: 简单
- **附件/URL**: `app.py` · `Dockerfile` · `docker-compose.yml` · `nc port.dyn.acsc.land 31582` · [平台](https://ctf.acsc.land/){target="_blank"}
- **附件链接**: [下载 app.py](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/safeshell/app.py){download} · [下载 Dockerfile](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/safeshell/Dockerfile){download} · [下载 docker-compose.yml](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/safeshell/docker-compose.yml){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/safeshell){target="_blank"}
- **Flag格式**: `dach2026{...}`
- **状态**: 已解

## Flag

```text
dach2026{should_have_used_aead_sademoji_f155g8el9sagwql0}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点既可以是本地附件 `app.py`，也可以直接连远程服务：`nc port.dyn.acsc.land 31582`
- `help` 菜单里最关键的命令是 `save` 和 `restore`
- `logon` 看似是管理员入口，但代码里实际逻辑为：

```python
elif cmd == "logon" and not state["admin"]:
    if arg == get_random_bytes(32).hex():  # TODO: hook up to DB
        print("Welcome Administrator!")
        state["admin"] = True
```

- 这里会在每次比较时重新生成一个随机 32 字节口令，因此正常交互下 **不可能通过 `logon` 进入管理员**

### 2. 关键突破点一
- 真正可利用的逻辑在 `save` / `restore`：

```python
elif cmd == "save":
    iv = get_random_bytes(16)
    pt = pad(json.dumps(state).encode(), 16)
    ct = iv + AES.new(KEY, AES.MODE_CBC, iv=iv).encrypt(pt)
    print(f"Saved shell state: {ct.hex()}")

elif cmd == "restore":
    ct = bytes.fromhex(arg)
    pt = AES.new(KEY, AES.MODE_CBC, iv=ct[:16]).decrypt(ct[16:])
    state = json.loads(unpad(pt, 16).decode())
```

- 服务端会把整个 `state` 以 **AES-CBC** 加密后交给用户
- `restore` 时又会直接解密并反序列化，没有任何 **MAC / 签名 / 完整性校验**
- 这意味着可以利用 **CBC 可篡改性（bit flipping）** 伪造管理员状态

### 3. 关键突破点二
- 初始状态为：

```python
state = {"admin": False, "notes": "use 'notes <your notes here>' to update notes!"}
```

- `json.dumps(state)` 的前 16 字节稳定为：

```text
{"admin": false,
```

- 我们希望把它改成同样 16 字节的：

```text
{"admin": true, 
```

- 对 CBC 第一块有：

$$
P_0 = D_k(C_0) \oplus IV
$$

- 因此只要把 IV 改成：

$$
IV' = IV \oplus P_0 \oplus P_0'
$$

- 就能在 **不知道密钥** 的情况下，把解密后的首块从 `false` 改为 `true`

对应字节串为：

```python
orig = b'{"admin": false,'
want = b'{"admin": true, '
new_iv = bytes(a ^ b ^ c for a, b, c in zip(iv, orig, want))
```

### 4. 获取 Flag
- 实际利用流程：
  1. 发送 `save` 获取十六进制密文
  2. 取出前 16 字节 `iv`
  3. 计算 `new_iv = iv ^ orig ^ want`
  4. 拼回 `new_iv + ciphertext_body`
  5. 用伪造密文执行 `restore`
  6. 发送 `flag`

- 服务端成功恢复后，`state["admin"]` 已经变成 `True`，于是直接回显 flag：

```text
Flag: dach2026{should_have_used_aead_sademoji_f155g8el9sagwql0}
```

## 攻击链/解题流程总结

```text
识别 logon 为伪入口 → 审计 save/restore 发现 AES-CBC 无完整性保护 → 保存 state 获取密文 → 对 IV 做 bit flipping 把 {"admin": false, 改为 {"admin": true,  → restore 伪造状态 → flag
```

## 漏洞分析 / 机制分析

### 根因
- **仅加密、不认证**：AES-CBC 只提供机密性，不提供完整性
- **把客户端可控密文当作可信状态恢复**：`restore` 直接反序列化解密结果
- **首块明文可预测**：`json.dumps(state)` 的起始结构稳定，方便精确构造 bit flip

### 影响
- 攻击者无需知道 AES 密钥，即可把任意可预测字段改写为希望的值
- 本题中可直接把 `admin` 从 `false` 提升为 `true`，从而读取敏感 flag
- 如果系统中还保存了其他权限字段、用户标识或计费状态，同样可能被篡改

### 修复建议（适用于漏洞类题目）
- 使用 **AES-GCM / ChaCha20-Poly1305** 等 AEAD 算法，为密文提供完整性校验
- 若必须使用 CBC，至少对 `iv || ciphertext` 再做 **HMAC** 校验
- 不要把权限状态整体交由客户端保存后恢复，改为 **服务端会话存储**
- 对解密后的对象做严格 schema 校验，避免“解密成功即可信”

## 知识点
- AES-CBC 的可篡改性（bit flipping）
- `P_i = D_k(C_i) \oplus C_{i-1}` / 首块 `P_0 = D_k(C_0) \oplus IV`
- AEAD 与“仅加密”方案的安全差异

## 使用的工具
- Python 标准库 `socket` / `re` — 远程交互与密文提取
- Python 字节运算 — 计算 `IV' = IV ^ orig ^ want`
- 本地阅读 `app.py` — 确认 JSON 结构和 CBC 加解密流程

## 脚本归档
- Go：[`ACSC2026Qualification_SafeShell.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/ACSC2026Qualification_SafeShell.go){target="_blank"}
- Python：[`ACSC2026Qualification_SafeShell.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/ACSC2026Qualification_SafeShell.py){target="_blank"}
- 说明：解题代码包含详细注释，可直接复现远程利用

## 命令行提取关键数据（无 GUI）

```bash
go run CTF_Writeups/scripts_go/ACSC2026Qualification_SafeShell.go -host port.dyn.acsc.land -port 31582

python CTF_Writeups/scripts_python/ACSC2026Qualification_SafeShell.py --host port.dyn.acsc.land --port 31582
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Go 标准库脚本 | 完整利用 | 秒级 | 单文件、无第三方依赖，适合归档 | 交互解析代码略长 |
| Python 标准库脚本 | 完整利用 | 秒级 | 无额外依赖，适合归档复现 | 需要自己处理交互 |
| `nc` | 手工探测 | 秒级 | 快速验证 banner / 命令回显 | 不方便直接做 XOR 篡改 |
| CyberChef / 十六进制计算器 | 快速验证异或公式 | 1-2 分钟 | 可视化，便于教学演示 | 远程自动化能力弱 |

### 推荐流程

**推荐流程**：先读 `app.py` 锁定 `save/restore` 逻辑 → 用 `save` 获取密文 → 用 Python 计算新 IV → `restore` 伪造管理员状态 → `flag`（秒级）。 

### 工具 A（推荐首选）
- **安装**：Python 3.10+
- **详细步骤**：
  1. 连接远程服务并执行 `save`
  2. 提取返回密文中的 `iv` 与密文主体
  3. 计算 `iv ^ b'{"admin": false,' ^ b'{"admin": true, '`
  4. 发送 `restore <forged_hex>`，再执行 `flag`
- **优势**：从分析到利用一体化，最适合写成可复现脚本

### 工具 B（可选）
- **安装**：任意支持十六进制 XOR 的可视化工具
- **详细步骤**：
  1. 先把原始 IV、`orig`、`want` 转成十六进制
  2. 逐字节异或得到新 IV
  3. 手工拼接伪造密文并发送给 `restore`
- **优势**：适合教学展示 CBC 首块篡改原理
