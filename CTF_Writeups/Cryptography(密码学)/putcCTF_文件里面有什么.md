# putcCTF - 文件里面有什么 Writeup

## 题目信息
- **比赛**: putcCTF
- **题目**: 文件里面有什么（beautiful）
- **类别**: Crypto / Stego
- **难度**: 中等
- **附件/URL**: `beautiful` · [Challenge](https://ctf.putcyberdays.pl/challenges){target="_blank"}
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/beautiful/beautiful){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/beautiful){target="_blank"}
- **CTFtime**: [Event #3202](https://ctftime.org/event/3202/){target="_blank"}
- **Flag格式**: `putcCTF{...}`
- **状态**: 复核中（提交串待确认）

## Flag（待最终提交确认）

```text
优先候选: putcCTF{chaos_blurring}
备选候选: putcCTF{CHAOS_BLURRING} / chaos_blurring / CHAOS_BLURRING
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点：附件 `beautiful`
- 文件头为 PNG，但在 `IEND` 之后仍有大量尾随数据，属于典型 polyglot/拼接载荷场景。

### 2. 关键突破点一
- 解析 PNG chunk，定位 `IEND` 结束偏移并提取 tail payload。
- 在 tail 中定位 ZIP 的 EOCD（`PK\x05\x06`），按 comment 长度裁剪出有效 ZIP，并分离出后续 JPEG 数据。
- 从 PNG 的 XMP 元数据提取 `<b64:c2lnbWEy>...</b64:c2lnbWEy>`，Base64 解码得到：`" Ishmael."`。

### 3. 关键突破点二
- 对 PNG RGB 三通道做 LSB 提取，按位拼装字节流。
- 将前缀按 UTF-16BE 解码，得到可读提示：`You can call me`。
- 拼接口令：`You can call me Ishmael.`，使用 AES ZIP 解压得到 `n01z.wav`。
- 对 WAV 生成频谱图，读取可视文本：`CHAOS_BLURRING`。

### 4. 获取 Flag
- 频谱文本核心内容为：`CHAOS_BLURRING`（分隔符为低频横线，判定更接近下划线 `_`）。
- 结合同赛事命名风格（`Exercise` 为小写内部串），优先提交：

```text
putcCTF{chaos_blurring}
```

## 攻击链/解题流程总结

```text
PNG 结构解析(IEND) → 提取尾随 payload → EOCD 裁剪 ZIP → XMP + RGB-LSB 组合口令 → 解压 WAV → 频谱读字 → Flag
```

## 漏洞分析 / 机制分析

### 根因
- 文件中叠加了多层信息隐藏通道（PNG 尾随、XMP 隐写、RGB-LSB、音频频谱）。
- 常规“单层提取”流程无法一次命中，必须分层拆解并串联线索。

### 影响
- 若分析者仅检查 PNG 可视内容，会遗漏关键载荷与后续密码线索。
- ZIP 口令需要多源提示拼接，任一链路缺失都会导致解密失败。

### 修复建议（适用于漏洞类题目）
- 上传侧对文件做严格格式重编码，去除尾随数据与非常规 metadata。
- 对媒体文件做 stego 检测（LSB 熵、频谱异常）并建立审计流程。
- 对压缩包口令与敏感数据传递采用独立安全通道，避免隐写泄露。

## 知识点
- PNG chunk 结构与 `IEND` 尾随数据提取
- ZIP EOCD 裁剪与 AES ZIP 解密
- RGB-LSB 位流恢复与 UTF-16BE 文本解码
- WAV 频谱隐写读取

## 使用的工具
- Python 3 — 自动化解析与解密流程
- `pyzipper` — AES ZIP 解密
- `Pillow` / `numpy` / `matplotlib` — LSB 提取与频谱图生成

## 脚本归档
- Go：待补（预计文件名：`putcCTF_文件里面有什么.go`）
- Python：[`putcCTF_文件里面有什么.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/putcCTF_%E6%96%87%E4%BB%B6%E9%87%8C%E9%9D%A2%E6%9C%89%E4%BB%80%E4%B9%88.py){target="_blank"}
- 说明：解题代码包含完整自动化复现流程

## 命令行提取关键数据（无 GUI）

```bash
python CTF_Writeups/scripts_python/putcCTF_文件里面有什么.py
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的对应类别工具推荐。

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| Python 脚本（本地） | 全流程复现 | 分钟级 | 可串联多层隐写链路，结果可归档 | 需手动读取频谱文本 |
| Security Hub MCP | 单点验证 | 秒级 | 适合快速验证文件与隐写方向 | 复杂链路仍需自定义脚本 |

### 推荐流程

**推荐流程**：先定位容器结构异常（IEND 尾随）→ 再提取 metadata/LSB 线索恢复口令 → 解压音频并频谱读字。 

### 工具 A（推荐首选）
- **安装**：Python 3 + `pyzipper pillow numpy matplotlib`
- **详细步骤**：
  1. 解析 PNG 并裁剪有效 ZIP
  2. 从 XMP 与 RGB-LSB 提取口令片段
  3. 解压 WAV 并生成频谱图读取文本
- **优势**：端到端可复现，便于后续沉淀同类题脚本

### 工具 B（可选）
- **安装**：启用 `security-hub` MCP
- **详细步骤**：
  1. 用 `forensic_file_type` / `stego_*` 做快速方向验证
  2. 确认后切换本地脚本做精确还原
- **优势**：前期筛查快，减少盲试成本
