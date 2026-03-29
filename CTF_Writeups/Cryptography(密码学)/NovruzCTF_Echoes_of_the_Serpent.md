# NovruzCTF - Echoes of the Serpent Writeup

## 题目信息
- **比赛**: NovruzCTF
- **题目**: Echoes of the Serpent
- **类别**: Cryptography
- **难度**: Easy-Medium
- **附件/URL**: `nc 95.111.234.103 1337` + 服务端源码 `f563fb06-e8e0-4279-8268-85d0cc835ba0.py`
- **Flag格式**: novruzCTF{}
- **状态**: 已解

## Flag

```text
novruzCTF{cbc_m4c_f0rg3ry_v14_l3ngth_3xt3ns10n}
```

## 解题过程

### 1. 分析服务端源码

连接服务后，服务端提供两条已知的 CBC-MAC：

```text
MAC('hello_world') = 77ec0fdf191b1011b974864b443a60ad
MAC('get_flag')    = 162cb90b16adeb0dcdc9776c3af7b324
```

要求：提交一条**新消息**（不能是已知的两条、且长度 > 16 字节），使其 CBC-MAC 正确。

审计源码关键点：
- 使用 AES-CBC 模式，IV 全零（`bytes(16)`）
- zero-padding：不足 16 字节时用 `\x00` 补齐
- CBC-MAC = CBC 加密后取最后一个密文块
- **没有使用 CMAC/OMAC 等安全 MAC 方案**

### 2. CBC-MAC 长度扩展攻击原理

CBC-MAC 对单块消息 $M_1$ 的计算：

$$\text{MAC}(M_1) = E_K(M_1 \oplus IV) = E_K(M_1 \oplus 0) = E_K(M_1)$$

对两块消息 $M_1 \| M_2$ 的计算：

$$C_1 = E_K(M_1 \oplus IV)$$

$$C_2 = E_K(M_2 \oplus C_1)$$

$$\text{MAC}(M_1 \| M_2) = C_2$$

**核心洞察**：如果我们已知 $\text{MAC}(M_1) = T_1$ 和 $\text{MAC}(M_2) = T_2$，可以构造：

$$M_{\text{forged}} = \text{pad}(M_1) \| (T_1 \oplus \text{pad}(M_2))$$

验证：

$$C_1 = E_K(\text{pad}(M_1) \oplus 0) = E_K(\text{pad}(M_1)) = T_1 \quad \text{(第一块加密结果就是 MAC}(M_1)\text{)}$$

$$C_2 = E_K((T_1 \oplus \text{pad}(M_2)) \oplus T_1) = E_K(\text{pad}(M_2)) = T_2 \quad \text{(XOR 消去 } T_1\text{)}$$

因此 $\text{MAC}(M_{\text{forged}}) = T_2 = \text{MAC}(M_2)$，伪造成功。

### 3. 构造伪造消息

已知：
- $M_1 = \text{"hello\_world"}$，padding 后 = `hello_world\x00\x00\x00\x00\x00`（16 字节）
- $T_1 = \text{MAC}(M_1) = \texttt{77ec0fdf191b1011b974864b443a60ad}$
- $M_2 = \text{"get\_flag"}$，padding 后 = `get_flag\x00\x00\x00\x00\x00\x00\x00\x00`（16 字节）
- $T_2 = \text{MAC}(M_2) = \texttt{162cb90b16adeb0dcdc9776c3af7b324}$

构造第二块：

$$\text{block}_2 = T_1 \oplus \text{pad}(\text{"get\_flag"})$$

$$= \texttt{77ec0fdf191b1011b974864b443a60ad} \oplus \texttt{6765745f666c61670000000000000000}$$

$$= \texttt{10897b807f777176b974864b443a60ad}$$

伪造消息：

$$M_{\text{forged}} = \text{pad}(\text{"hello\_world"}) \| \text{block}_2$$

$$= \texttt{68656c6c6f5f776f726c640000000000}\texttt{10897b807f777176b974864b443a60ad}$$

伪造 MAC = $T_2 = \texttt{162cb90b16adeb0dcdc9776c3af7b324}$

### 4. 获取 Flag

```text
$ nc 95.111.234.103 1337
Prophecy (Hex Msg)> 68656c6c6f5f776f726c64000000000010897b807f777176b974864b443a60ad
Seal (Hex Token)> 162cb90b16adeb0dcdc9776c3af7b324
[+] The gates open! The serpent rewards you: novruzCTF{cbc_m4c_f0rg3ry_v14_l3ngth_3xt3ns10n}
```

## 攻击链/解题流程总结

$$\text{审计源码} \rightarrow \text{识别长度扩展漏洞} \rightarrow T_1 \oplus \text{pad}(M_2) \text{ 构造第二块} \rightarrow \text{拼接} M_{\text{forged}} \rightarrow \text{提交} + T_2 \rightarrow \text{Flag}$$

## 漏洞分析 / 机制分析

### 根因
CBC-MAC **不是**长度安全的 MAC。对于变长消息，攻击者知道 $\text{MAC}(M_1)$ 和 $\text{MAC}(M_2)$ 后可以构造 $\text{MAC}(M_1 \| X) = \text{MAC}(M_2)$。根本原因在于 CBC 链式结构允许攻击者通过 XOR 操作控制中间状态。

### 影响
- 攻击者可以伪造任意长度的消息的 MAC
- 认证机制完全被绕过

### 修复建议
1. 使用 **CMAC**（基于 CBC-MAC 的安全变体，RFC 4493）
2. 使用 **HMAC**（基于哈希函数的 MAC）
3. 使用 **GMAC**（GCM 模式的 MAC）
4. 如果必须用 CBC-MAC，先对消息长度做前缀编码（Encrypt-then-MAC）

## 知识点
- CBC-MAC 长度扩展攻击（Length Extension Attack）
- CBC 模式的链式 XOR 结构
- Zero-padding 的安全问题（不具有唯一可逆性）
- MAC 伪造（Forgery）

## 使用的工具
- Python 3 + pwntools/手工计算 — 构造伪造消息
- netcat (`nc`) — 连接远程服务

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_Echoes_of_the_Serpent.go`
- Python：`CTF_Writeups/scripts_python/echoes_of_the_serpent.py`

## 命令行提取关键数据（无 GUI）

```bash
# 连接服务获取 MAC 值
nc 95.111.234.103 1337

# 手工计算 XOR（Python 单行）
python3 -c "
t1=bytes.fromhex('77ec0fdf191b1011b974864b443a60ad')
m2=b'get_flag'+b'\x00'*8
b2=bytes(a^b for a,b in zip(t1,m2))
msg=b'hello_world'+b'\x00'*5+b2
print('Msg:',msg.hex())
print('MAC: 162cb90b16adeb0dcdc9776c3af7b324')
"

# 提交伪造消息
echo -e "68656c6c6f5f776f726c64000000000010897b807f777176b974864b443a60ad\n162cb90b16adeb0dcdc9776c3af7b324" | nc 95.111.234.103 1337
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Python 手工脚本 | XOR 计算+提交 | ~2 min | 灵活、快速 | 需要手动处理 |
| Go 脚本 | XOR 计算 | ~3 min | 类型安全、可复用 | 网络交互稍繁琐 |
| CyberChef | XOR 可视化 | ~1 min | 直观 | 不便自动化 |

### 推荐流程

**推荐流程**：审计源码 → CyberChef XOR 计算 → nc 提交（预估 3-5 分钟）。

### CyberChef（推荐首选，最快）
- **地址**：https://gchq.github.io/CyberChef/
- **详细步骤**：
  1. **From Hex** — 输入 $T_1 = \texttt{77ec0fdf191b1011b974864b443a60ad}$，得到原始字节
  2. **XOR** — Key 设为 `get_flag\x00\x00\x00\x00\x00\x00\x00\x00`（即 `pad("get_flag")` 的 hex：`6765745f666c61670000000000000000`，Key 格式选 Hex）
  3. **To Hex** — 输出即为 block2 = `10897b807f777176b974864b443a60ad`
  4. 手动拼接：`pad("hello_world")` 的 hex `68656c6c6f5f776f726c640000000000` + block2
  5. 最终提交：消息 = `68656c6c6f5f776f726c64000000000010897b807f777176b974864b443a60ad`，MAC = `162cb90b16adeb0dcdc9776c3af7b324`
- **CyberChef Recipe 链接**：`From_Hex('None')` → `XOR({'option':'Hex','string':'6765745f666c61670000000000000000'})` → `To_Hex('None')`
- **优势**：全程可视化，无需写代码，~1 分钟完成 XOR 计算

### Python 脚本（可选）
- **安装**：仅需标准库
- **详细步骤**：
  1. 解析服务端返回的两个 MAC 值
  2. 计算 $T_1 \oplus \text{pad}(M_2)$ 得到第二块
  3. 拼接 $\text{pad}(M_1) \| \text{block}_2$ 并提交
- **优势**：代码简洁，bytes 操作方便

### Go 脚本（可选）
- **安装**：Go 1.25+
- **详细步骤**：见 `CTF_Writeups/scripts_go/echoes_of_the_serpent.go`
- **优势**：类型安全，适合集成到 CTF 工具集
