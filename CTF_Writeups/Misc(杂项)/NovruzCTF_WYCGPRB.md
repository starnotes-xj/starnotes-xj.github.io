# novruzCTF - Ancient Spell (Misc/Stego)

## 题目信息

- **题目名称**: WYCGPRB（西约克郡政府公共关系委员会）
- **类别**: Misc / Steganography
- **难度**: 难
- **题目描述**: 在遥远的群山中，居住着一个古老的部落。据说他们的祖先曾传授一个神奇的咒语，但随着时间的流逝，这个咒语早已被遗忘。他们唯一留下的，是一段神秘的录音，其含义无人能解。请从这段录音中找到那个神奇的咒语。
- **附件**: `7630e312-da5e-4792-9f88-d02a7494a651.wav`
- **状态**: 已解

## Flag

```text
novruzCTF{R3DB0X3920}
```

## 解题过程

### 1. 文件基本分析

```bash
$ file 7630e312-da5e-4792-9f88-d02a7494a651.wav
RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 44100 Hz
```

| 属性 | 值 |
|------|------|
| 格式 | WAV (PCM 16bit) |
| 声道 | 单声道 (Mono) |
| 采样率 | 44100 Hz |
| 时长 | 111.34 秒 |
| 文件大小 | ~9.8 MB |

关键观察：音频时长约 111 秒，信号连续无静音段，频率范围集中在 **1100-2300 Hz** —— 这是 SSTV（慢扫描电视）信号的典型特征。

### 2. 识别 SSTV 信号

对音频前 500ms 进行 5ms 窗口的频率分析：

```text
  0-100ms:  1900 Hz  ← SSTV Leader 音
100-200ms:  1500 Hz  ← 校准信号
200-300ms:  1900 Hz  ← SSTV Leader 音
300-400ms:  1500 Hz  ← 校准信号
400-500ms:  2300 Hz  ← 图像数据（白色）
```

**1900 Hz Leader + 1500-2300 Hz 图像数据** 完全符合 SSTV 协议：

- **1200 Hz** = 同步脉冲 (Sync)
- **1500 Hz** = 黑色 (Black)
- **1900 Hz** = Leader/校准音
- **2300 Hz** = 白色 (White)

### 3. 确定 SSTV 模式

通过分析 VIS（Vertical Interval Signal）码和同步脉冲间距：

**VIS 码解码**（1410-1720ms 区间）：

| 时间段 | 频率 | 含义 |
|--------|------|------|
| 1410-1440ms (30ms) | 1200 Hz | VIS Start Bit |
| 1440-1500ms (60ms) | 1300 Hz | Bit 0,1 = 1,1 |
| 1500-1620ms (120ms) | 1100 Hz | Bit 2,3,4,5 = 0,0,0,0 |
| 1620-1680ms (60ms) | 1300 Hz | Bit 6 + Parity = 1,1 |
| 1680-1720ms (30ms+) | 1200 Hz | VIS Stop Bit |

**同步脉冲间距** = **428ms**，与 **Scottie S1** 模式完全匹配：

| 参数 | Scottie S1 标准值 |
|------|-------------------|
| 行时间 | 428.22 ms |
| 同步脉冲 | 1200 Hz, 9ms |
| 色彩扫描 | 138.24 ms / 通道 |
| 分隔符 | 1500 Hz, 1.5ms |
| 图像尺寸 | 320 x 256 |
| 通道顺序 | Green, Blue, Red |

### 4. 编写 SSTV 解码器

由于没有现成 SSTV 解码软件，手写 Python 解码器。核心逻辑：

```python
# 频率估计：零交叉法 + 线性插值
def get_freq(pos, half_w=15):
    chunk = samples[pos-half_w : pos+half_w]
    crossings = []
    for i in range(1, len(chunk)):
        if (chunk[i-1] >= 0) != (chunk[i] >= 0):
            frac = chunk[i-1] / (chunk[i-1] - chunk[i])
            crossings.append(i - 1 + frac)
    periods = [crossings[i] - crossings[i-1] for i in range(1, len(crossings))]
    return sample_rate / (2 * avg(periods))

# 频率 → 像素映射 (SSTV 标准)
def freq_to_pixel(freq):
    return clamp((freq - 1500) / 800 * 255, 0, 255)

# Scottie S1 逐行解码
for line in range(256):
    line_start = first_sync + line * samples_per_line
    green_start = line_start + sync_samples + porch_samples
    blue_start  = green_start + color_samples + sep_samples
    red_start   = blue_start  + color_samples + sep_samples

    for x in range(320):
        frac = x / 320
        G = freq_to_pixel(get_freq(green_start + frac * color_samples))
        B = freq_to_pixel(get_freq(blue_start  + frac * color_samples))
        R = freq_to_pixel(get_freq(red_start   + frac * color_samples))
        image[x, line] = (R, G, B)
```

### Go 版本解题脚本（bi/bo → 摩尔斯）

> 假设已用 SSTV 工具得到文本（对话气泡中的 `bi/bo`），该 Go 脚本完成最后的摩尔斯解码。

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

var morseMap = map[string]string{
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z", "-----": "0", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9",
}

func decodeWord(w string) string {
    parts := []string{}
    for i := 0; i < len(w); {
        if strings.HasPrefix(w[i:], "bi") {
            parts = append(parts, ".")
            i += 2
        } else if strings.HasPrefix(w[i:], "bo") {
            parts = append(parts, "-")
            i += 2
        } else {
            i++
        }
    }
    morse := strings.Join(parts, "")
    if v, ok := morseMap[morse]; ok {
        return v
    }
    return "?"
}

func main() {
    in := bufio.NewScanner(os.Stdin)
    for in.Scan() {
        line := strings.TrimSpace(in.Text())
        if line == "" {
            continue
        }
        words := strings.Fields(line)
        out := strings.Builder{}
        for _, w := range words {
            out.WriteString(decodeWord(w))
        }
        fmt.Println(out.String())
    }
}
```

**使用方式**：
```bash
# 将对话气泡里的文本保存为 bi_bo.txt

go run decode_bibo.go < bi_bo.txt
```

**优化措施**：
- 三通道灰度平均，降低单通道噪声
- 中值滤波去除脉冲噪点
- 自动对比度增强文字可读性

### 5. 解码图像内容

解码后获得一张 320x256 的图像：一个人的自拍照，左上方有一个**对话气泡**，里面包含编码文字：

```text
bibobi bibibibobo bobibi
bobibibi bobobobobo
bobibibo bibibibobo
bobobobobi bibibobobo
bobobobobo
```

### 6. 解码摩尔斯电码

文字使用 **"bi"（点/dit）** 和 **"bo"（划/dah）** 表示摩尔斯电码：

| 编码单词 | bi/bo 分解 | 摩尔斯 | 字符 |
|----------|-----------|--------|------|
| bibobi | bi-bo-bi | .-. | **R** |
| bibibibobo | bi-bi-bi-bo-bo | ...-- | **3** |
| bobibi | bo-bi-bi | -.. | **D** |
| bobibibi | bo-bi-bi-bi | -... | **B** |
| bobobobobo | bo-bo-bo-bo-bo | ----- | **0** |
| bobibibo | bo-bi-bi-bo | -..- | **X** |
| bibibibobo | bi-bi-bi-bo-bo | ...-- | **3** |
| bobobobobi | bo-bo-bo-bo-bi | ----. | **9** |
| bibibobobo | bi-bi-bo-bo-bo | ..--- | **2** |
| bobobobobo | bo-bo-bo-bo-bo | ----- | **0** |

**解码结果**: `R3DB0X3920`

## 漏洞分析 / 机制分析

本题为音频隐写/编码识别题，无漏洞利用，核心机制为 SSTV 信号调制与摩尔斯变体编码。

## 知识点总结

### SSTV（Slow Scan Television）

SSTV 是一种通过音频信号传输静态图像的技术，广泛用于业余无线电。核心原理：

- **频率调制 (FM)**：将像素亮度映射为音频频率（1500 Hz = 黑，2300 Hz = 白）
- **逐行扫描**：每行按 R/G/B 通道依次传输
- **同步脉冲**：1200 Hz 短脉冲标记每行起始
- **VIS 码**：开头的数字编码标识 SSTV 模式（如 Scottie S1、Martin M1 等）

常见 SSTV 模式与时长：

| 模式 | 行时间 | 总时长 | 分辨率 |
|------|--------|--------|--------|
| Scottie S1 | 428ms | ~110s | 320x256 |
| Martin M1 | 446ms | ~114s | 320x256 |
| Robot 36 | - | ~36s | 320x240 |

### 摩尔斯电码变体编码

本题使用 "bi"/"bo" 代替传统的 "."/"−"，属于摩尔斯电码的**音节变体编码**：

- **bi** = dit (短信号/点)
- **bo** = dah (长信号/划)

这种编码方式在 CTF 中偶尔出现，关键是识别出两个交替出现的音节对应摩尔斯的点和划。

## 使用的工具

| 工具 | 用途 |
|------|------|
| Python + wave 模块 | 读取 WAV 音频数据 |
| 自编 SSTV 解码器 | 频率分析 + Scottie S1 图像解码 |
| Pillow (PIL) | 图像生成、裁剪、对比度增强 |
| 零交叉法频率估计 | 从时域信号提取瞬时频率 |

## 脚本归档
- Go：`CTF_Writeups/scripts_go/NovruzCTF_WYCGPRB.go`
- Python：`CTF_Writeups/scripts_python/NovruzCTF_WYCGPRB.py`

## 命令行提取关键数据（无 GUI）

```bash
# 先用频谱图快速确认 SSTV 特征
sox 7630e312-da5e-4792-9f88-d02a7494a651.wav -n spectrogram -o sstv_spec.png

# 将音频转为单声道 44100Hz（保证解码器兼容）
ffmpeg -y -i 7630e312-da5e-4792-9f88-d02a7494a651.wav -ac 1 -ar 44100 sstv.wav
```

## 推荐工具与优化解题流程

> 参考 `CTF_TOOLS_EXTENSION_PLAN.md` 中的 Stego 工具推荐。本题涉及音频隐写（SSTV）和摩尔斯电码解码。

### 1. QSSTV / RX-SSTV — SSTV 专用解码器（推荐首选）

专用的 SSTV 解码软件可以一键解码音频为图像，无需手写解码器。

**QSSTV（Linux）安装：**
```bash
sudo apt install qsstv
```

**详细操作步骤：**

**Step 1：配置音频输入**
1. 启动 QSSTV
2. Options → Configuration → Sound → 选择音频输入设备
3. 或者使用 PulseAudio 虚拟设备播放 WAV 文件

**Step 2：解码 SSTV 信号**
1. 点击 "Receive" 开始接收
2. 用音频播放器播放 WAV 文件（通过虚拟设备路由到 QSSTV）
3. QSSTV 自动识别 SSTV 模式（Scottie S1）并开始解码
4. ~110 秒后完整图像显示在界面中

**Step 3：另一种方法 — 直接解码文件**
```bash
# 使用 SSTV Python 库
pip install sstv
sstv -d 7630e312-da5e-4792-9f88-d02a7494a651.wav -o decoded.png
```

**优势**：自动识别 SSTV 模式，无需手动解析 VIS 码和同步脉冲，约 2 分钟出图。

---

### 2. Sonic Visualiser — 音频频谱分析

[Sonic Visualiser](https://www.sonicvisualiser.org/) 是音频隐写分析的必备工具。

**安装：**
```bash
# macOS
brew install sonic-visualiser
# Linux
sudo apt install sonic-visualiser
```

**详细操作步骤：**

**Step 1：加载音频文件**
1. 启动 Sonic Visualiser → File → Open → 选择 WAV 文件

**Step 2：添加频谱图层**
1. Layer → Add Spectrogram → 选择 "All Channels Mixed"
2. 调整参数：Window Size = 1024, Colour = Green
3. 频谱图会清晰显示 1100-2300 Hz 范围的 SSTV 信号

**Step 3：识别 SSTV 特征**
- 频谱图中可以看到：
  - **1900 Hz 水平线** = Leader 音
  - **1200 Hz 短脉冲** = 同步信号（每 428ms 一次）
  - **1500-2300 Hz 变化区域** = 图像数据
- 从频谱图可以直观判断这是 SSTV 信号，而非其他隐写方式

**优势**：快速判断音频类型（SSTV/DTMF/频谱图隐写），频谱可视化一目了然。

---

### 3. CyberChef — 摩尔斯电码解码

[CyberChef](https://gchq.github.io/CyberChef/) 内置摩尔斯电码解码器。

**详细操作步骤：**

**Step 1：将 bi/bo 转换为标准摩尔斯**
1. 打开 CyberChef
2. 使用 "Find / Replace" 操作：
   - `bi` → `.`
   - `bo` → `-`
3. 添加空格分隔符（每个单词之间）

**Step 2：摩尔斯解码**
1. 添加 "From Morse Code" 操作
2. 设置分隔符（Letter: 空格, Word: 换行）
3. 输出: `R3DB0X3920`

**CyberChef 配方：**
```text
Find_/_Replace({'option':'Regex','string':'bo'},'_',true,false,true,false)
Find_/_Replace({'option':'Regex','string':'bi'},'.',true,false,true,false)
From_Morse_Code('Space','Line feed')
```

**优势**：在线可视化操作，拖拽即可完成编码转换。

---

### 4. Binwalk — 文件分析（排除法）

```bash
# 检查 WAV 文件中是否嵌入了其他文件
binwalk 7630e312-da5e-4792-9f88-d02a7494a651.wav

# 如果有嵌入文件，自动提取
binwalk -e 7630e312-da5e-4792-9f88-d02a7494a651.wav
```

**用途**：快速排除文件末尾附加数据等简单隐写方式。

---

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 |
|------|---------|---------|------|
| **QSSTV / sstv 库** | SSTV 解码 | ~2 分钟 | 自动识别模式并解码，无需手写解码器 |
| **Sonic Visualiser** | 音频类型识别 | ~1 分钟 | 频谱图直观判断信号类型 |
| **CyberChef** | 摩尔斯解码 | ~30 秒 | 在线操作，无需编程 |
| **Binwalk** | 初步分析 | ~10 秒 | 快速排除简单隐写 |
| **手写 Python 解码器** | 完整解码 | ~1 小时 | 学习价值高，但耗时很长 |

**推荐流程**：Sonic Visualiser 确认 SSTV → QSSTV/sstv 库解码图像 → 肉眼读取 bi/bo 文字 → CyberChef 摩尔斯解码 → 5 分钟内完成（对比手写解码器的 1 小时）。

## 解题流程图

```text
WAV 音频文件
    │
    ▼
频率分析 (1100-2300 Hz 范围)
    │
    ▼
识别为 SSTV 信号 (1900Hz Leader)
    │
    ▼
VIS 码 + 同步脉冲 → 确认 Scottie S1 模式
    │
    ▼
自编解码器 → 320x256 RGB 图像
    │
    ▼
对话气泡中提取 bi/bo 编码文字
    │
    ▼
bi=dot, bo=dash → 摩尔斯电码解码
    │
    ▼
R3DB0X3920 → novruzCTF{R3DB0X3920}
```
