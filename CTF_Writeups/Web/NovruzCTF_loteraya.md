# NovruzCTF 2026 - Lottery (Web/Crypto) [未解决]

## 题目信息
- **题目**: 科西亚和鲍尔迪创办了一个彩票，从中赚取了巨额财富。这个彩票系统会被黑客攻击吗？
- **地址**: `http://95.111.234.103:2900/`
- **Flag格式**: `NovruzCTF{}`
- **分类**: Web
- **状态**: **未解决** - 仍在寻找正确 flag

## 已确认信息

### 技术栈
- **后端**: Express.js (Node.js)
- **RSA库**: NodeRSA
- **Session**: cookie-session 中间件（Keygrip HMAC-SHA1 签名）
- **Cookie**: `session` + `session.sig`（27字符 base64url 签名）
- **服务路径**: `/usr/src/app/server.js`（Docker 容器），第43行使用 NodeRSA.importKey

### Session Cookie 结构
Base64 解码 `session` cookie：
```json
{
  "key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
  "task": {"n": "...", "e": 65537, "c": "..."},
  "correctAnswers": 0
}
```
- RSA 私钥直接存储在客户端 Cookie 中
- `correctAnswers` 每次正确回答 +1
- `task` 包含 RSA 参数（n, e）和密文 c

### RSA 参数
- **密钥长度**: 512-bit
- **填充方式**: OAEP
- **密文**: 128 字节 = 2个 OAEP 块（每块 64 字节）
- **明文格式**: `"I placed X slons or no"`，X 在 -1000 到 1000 之间

### API 端点
- `GET /` - 主页，显示 RSA challenge
- `GET /generate-task` - 生成新任务，返回 JSON + 设置 session cookie
- `POST /check-task` - 提交答案，JSON body `{"input": "数字"}`
- 响应包含: `success`, `answered`, `task`(新任务)

## 已尝试的攻击方法

### 1. RSA 自动解密 + 大量回答 ✓（技术成功，但不产出 flag）
- 可无限自动解密并正确回答
- 测试了 1000+ 轮，服务器永远只返回新任务，无 flag
- **结论**: 单纯增加 correctAnswers 轮数不是解法

### 2. Cookie 签名密钥暴力破解 ✗
- 使用 Node.js Keygrip 库验证（确保算法完全一致）
- 测试了 cookie-monster 工具字典（289 条）
- 测试了 SecLists 密码字典
- 自定义字典（CTF 相关、Express 常见密钥、数字 0-999999 等）
- **总计 200k+ 密码候选，均未成功**
- 相关脚本: `crack_cookie.js`, `crack_cookie2.js`

### 3. JSON Prototype Pollution ✗
- 通过 `__proto__` 注入: `{"__proto__": {"correctAnswers": 99999, "isAdmin": true}}`
- 通过 `constructor.prototype`: `{"constructor": {"prototype": {...}}}`
- 嵌套 `__proto__`
- 设置各种属性: threshold, minScore, requiredAnswers, flag, win
- **服务器接受请求但无全局效果**

### 4. qs-style URL-encoded Prototype Pollution（待验证结果）
- Express 的 `urlencoded` body parser 使用 `qs` 库
- 发送 `Content-Type: application/x-www-form-urlencoded`
- 载荷: `input=123&__proto__[correctAnswers]=99999`
- **最后一次测试已运行完成，结果未查看**

### 5. 端口扫描（部分成功但 flag 错误）
- 端口 3000 返回了一个 flag: `novruzctf{Pr0t0type_P0lluti0n_1s_N0t_Just_f0r_Adm1n_Access}`
- **但这个 flag 属于 Ghost Machine 题目，不是 Lottery 题目！**
- 提交后被判定错误

### 6. 其他尝试 ✗
- 路径遍历 — 无结果
- 各种查询参数（debug, flag, admin, getFlag 等）— 无结果
- 多种 HTTP 方法（PUT, PATCH）到不同端点 — 无结果
- Session 伪造（修改 correctAnswers 后重新签名）— 无法绕过签名验证

## 漏洞分析 / 机制分析
- **客户端保存私钥**：session cookie 中包含 RSA 私钥与题目参数，逻辑上不安全，但目前未找到可直接利用的越权路径。
- **cookie-session HMAC**：签名强度足以阻止伪造，未发现弱密钥。
- **原型污染线索**：存在可疑 JSON 处理路径，但尚未确认可影响到服务端逻辑或 flag 判定。
- **结论**：尚未定位最终漏洞触发条件，需要进一步验证（待补）。

## 关键脚本

### 主解题脚本
`solve_rsa_lottery.py` - Python，自动解密 RSA + 测试各种原型污染

### Cookie 破解脚本
- `crack_cookie.js` - Node.js，使用 Keygrip 库 + 大字典
- `crack_cookie2.js` - Node.js，精简版 + 自生成数字密码

### 其他文件
- `get_cookie.py` - 获取原始 session cookie
- `secrets.lst` - cookie-monster 密钥字典
- `cm_tool/` - cookie-monster 工具仓库

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_loteraya.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_loteraya.py`

## 待尝试的方向

### 高优先级
1. **检查 qs-style 原型污染结果** — 最后一次测试的输出未查看
2. **深入原型污染** — 尝试污染更多属性，如 `outputFunctionName`（模板注入 RCE）
3. **Session 重放/竞态条件** — 同时发送多个请求，看是否有竞态漏洞
4. **仔细分析 /check-task 响应** — 是否在某个 correctAnswers 阈值返回额外字段

### 中优先级
5. **更大的密钥字典** — 尝试 rockyou.txt 等大型字典
6. **SSRF/内部请求** — 是否有端点接受 URL 参数
7. **WebSocket** — 检查是否有 WebSocket 端点
8. **JWT/其他认证** — 是否有其他认证机制

### 低优先级
9. **源码泄露** — 尝试 `.git/`, `package.json`, `server.js` 等路径
10. **DNS/域名** — 检查域名解析和虚拟主机

## 使用的工具
- Python（PyCryptodome）— RSA OAEP 解密与自动答题
- Node.js（Keygrip）— cookie-session 签名验证与爆破尝试
- curl — 获取 cookie 与接口调用
- cookie-monster — HMAC 字典爆破

## 命令行提取关键数据（无 GUI）

```bash
# 获取 session cookie
curl -i http://95.111.234.103:2900/generate-task | rg -i "set-cookie: session="

# 解码 base64url 的 session（需要替换字符后再 base64 -d）
# echo '<session_value>' | tr '_-' '/+' | base64 -d
```

## 推荐工具与优化解题流程

### 推荐工具
- **RsaCtfTool**：若题目变体是 RSA 弱点，可快速尝试常见攻击
- **CyberChef**：快速检查 base64/url 编码、数据字段

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **RsaCtfTool** | RSA 弱点探测 | 视情况 | 常见攻击一键化 | 仅适用于弱密钥
| **CyberChef** | 数据解码 | ~1 分钟 | 可视化快 | 自动化不足
| **自写脚本** | 任务解密/验证 | ~5 分钟 | 可定制 | 需要维护

### 推荐流程
**推荐流程**：先用自写脚本解密任务 → 再用 CyberChef/脚本检查字段 → 若疑似弱密钥再用 RsaCtfTool 验证（当前未解，待补）。

## RSA 解密核心代码

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

def decrypt_task(task, pem_key):
    key = RSA.import_key(pem_key)
    c_bytes = base64.b64decode(task['c'])
    block_size = key.size_in_bytes()  # 64 for 512-bit
    plaintext = b''
    for i in range(0, len(c_bytes), block_size):
        cipher = PKCS1_OAEP.new(key)
        plaintext += cipher.decrypt(c_bytes[i:i+block_size])
    return plaintext.decode('utf-8')
```

**Go 版本（RSA OAEP 解密）**：
```go
package main

import (
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha1"
    "crypto/x509"
    "encoding/base64"
    "encoding/pem"
    "fmt"
)

func decryptTask(cipherB64, pemKey string) (string, error) {
    block, _ := pem.Decode([]byte(pemKey))
    if block == nil {
        return "", fmt.Errorf("invalid pem")
    }
    priv, err := x509.ParsePKCS8PrivateKey(block.Bytes)
    if err != nil {
        return "", err
    }
    key := priv.(*rsa.PrivateKey)
    cBytes, _ := base64.StdEncoding.DecodeString(cipherB64)
    hash := sha1.New() // NodeRSA 默认 OAEP-SHA1
    out := make([]byte, 0)
    for i := 0; i < len(cBytes); i += key.Size() {
        part, err := rsa.DecryptOAEP(hash, rand.Reader, key, cBytes[i:i+key.Size()], nil)
        if err != nil {
            return "", err
        }
        out = append(out, part...)
    }
    return string(out), nil
}
```

## Cookie 签名验证

```python
import hmac, hashlib, base64

def compute_sig(cookie_val, secret):
    sig = hmac.new(secret.encode('utf-8'), cookie_val.encode('utf-8'), hashlib.sha1).digest()
    return base64.b64encode(sig).decode('utf-8').rstrip('=').replace('+', '-').replace('/', '_')
```

**Go 版本（cookie-session 签名）**：
```go
package main

import (
    "crypto/hmac"
    "crypto/sha1"
    "encoding/base64"
    "strings"
)

func computeSig(val, secret string) string {
    mac := hmac.New(sha1.New, []byte(secret))
    mac.Write([]byte(val))
    sum := mac.Sum(nil)
    sig := base64.StdEncoding.EncodeToString(sum)
    sig = strings.TrimRight(sig, "=")
    sig = strings.ReplaceAll(sig, "+", "-")
    sig = strings.ReplaceAll(sig, "/", "_")
    return sig
}
```

## 知识点
- **RSA OAEP 分块解密** — 512-bit 密钥下密文需要按块解密
- **cookie-session 签名机制** — HMAC-SHA1 + base64url
- **原型污染** — JSON/qs 处理路径可能影响全局对象
- **CTF 多题共用环境** — 端口/flag 可能属于不同题目

## 教训
1. **端口 3000 的 flag 不是这道题的** — 同一服务器可能运行多个独立题目
2. **单纯增加回答轮数无效** — Web 题需要找 Web 漏洞
3. **cookie-session 签名非常强** — HMAC-SHA1 + 未知密钥 = 极难伪造
4. **原型污染是关键线索** — flag 名称明确提到 Prototype Pollution，但具体利用方式尚未找到
