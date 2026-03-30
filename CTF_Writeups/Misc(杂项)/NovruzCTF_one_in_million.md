# novruzCTF - Needle in a Haystack (Misc)

## 题目信息

- **题目名称**: Needle in a Haystack（大海捞针）
- **类别**: Misc
- **难度**: 中等
- **Flag格式**: `novruzCTF{}`
- **题目描述**: 人们常说大海捞针是不可能的，但对电脑来说，这只是一个普通的星期二。种子密钥隐藏在 1000 到 100 万之间。别再手动猜测了，让你的 CPU 来完成烧录。找到那个至关重要的种子密钥。
- **附件**: `a87ad61f-e3a0-4547-a92c-e7957eaade3c.png`（150x150 RGB 图片）
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/one%20in%20million/a87ad61f-e3a0-4547-a92c-e7957eaade3c.png){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/one%20in%20million){target="_blank"}
- **状态**: 进行中

## 解题过程

### 1. 图片分析

拿到的是一张 150×150 的 RGB PNG 图片，视觉上看全是噪声/杂色。

进行像素统计分析后发现关键特征：

| 属性 | 值 |
|------|-----|
| 尺寸 | 150×150 |
| 模式 | RGB |
| 像素值范围 | 0-51（而非正常的 0-255）|
| R 通道范围 | 0-50（51 个唯一值）|
| G 通道范围 | 0-51（52 个唯一值，值 51 仅出现 4 次）|
| B 通道范围 | 0-50（51 个唯一值）|
| 值分布 | 0-50 均匀分布（每个值约 1300 次），51 仅 4 次 |

**关键发现**：像素值被限制在 0-50 范围内，值 51 仅在 G 通道出现 4 次。这强烈暗示噪声是通过某种 `seed` 控制的 PRNG 以 `randint(0, 50)` 或类似方法生成的。

G=51 的 4 个像素位置：
- (75, 3): RGB=(33, 51, 21)
- (33, 39): RGB=(28, 51, 39)
- (129, 123): RGB=(2, 51, 38)
- (132, 131): RGB=(17, 51, 48)

### 2. 暴力破解思路

题目明确提示种子范围 1000-1000000，需要 CPU 暴力搜索。核心问题是确定：
1. 使用了什么 PRNG（Python random / numpy / Go rand / C rand / 哈希等）
2. 噪声生成方式（`randint(0, N)` / `randbytes` / `random()` 等）
3. 编码操作（XOR / 加法取模 / 像素打乱 shuffle 等）

## 漏洞分析 / 机制分析
- **机制假设**：图像噪声由 PRNG 生成，seed 位于 1000-1000000。
- **证据**：像素值范围被限制在 0-51，且分布均匀，符合随机噪声特征。
- **验证重点**：PRNG 实现与像素生成/混淆方式（XOR、取模、shuffle、hash）。
- **状态**：尚未确定真实生成方式，待补关键验证结果。

### 3. 已排除的方法

#### Python random 模块（所有方法均未命中）

| 方法 | 操作 | 结果 |
|------|------|------|
| `randint(0, 50)` | 直接匹配 / 减法取模 | ✗ |
| `randint(0, 51)` | 直接匹配 | ✗ |
| `randint(0, 255)` | XOR | ✗ |
| `randint(0, 255) % 52` | 匹配 | ✗ |
| `randbytes()` | XOR | ✗ |
| `int(random()*51)` | 匹配 | ✗ |
| `int(random()*52)` | 匹配 | ✗ |
| `getrandbits(8)%51` | 匹配 | ✗ |
| `getrandbits(6)` | 匹配 | ✗ |
| `randrange(51)` | 匹配 | ✗ |

#### numpy random

| 方法 | 操作 | 结果 |
|------|------|------|
| `RandomState(seed).randint(0,256)` | XOR | ✗ |
| `default_rng(seed).integers(0,256)` | XOR | ✗ |

#### Go math/rand

| 方法 | 操作 | 结果 |
|------|------|------|
| `Intn(256)` | XOR | ✗ |
| `Intn(51)` | 减法取模 | ✗ |
| Fisher-Yates shuffle | 像素位置解密 | 进行中... |

#### 其他

| 方法 | 操作 | 结果 |
|------|------|------|
| 常数 XOR (0-255) | `pixel ^ key` | ✗ |
| 常数偏移取模 | `(pixel - offset) % mod` | ✗ |
| SHA256 哈希噪声 | `sha256(seed||index)[0] % 51` | 进行中... |
| MD5 哈希噪声 | `md5(seed||index)[0] % 51` | 进行中... |

### 4. 待尝试方向

- [ ] C/glibc LCG `rand()` (`srand(seed); rand() % 51`)
- [ ] MSVC LCG `rand()` (Windows 平台差异)
- [ ] Python `random.shuffle` 像素位置打乱（需要在 Go 中实现 Python MT19937）
- [ ] 多字节 seed 用法（如 `seed` 转 bytes 后作为 key）
- [ ] AES/RC4 流密码用 seed 作为密钥
- [ ] `seed` 不是 PRNG 种子而是某种数学密钥
- [ ] 图片可能需要结合其他未发现的附件

## 知识点
- **PRNG 种子暴力** — 给定范围可并行搜索
- **像素分布分析** — 值域收缩提示取模或截断
- **定位异常像素** — 稀有值可作为校验锚点

### 5. 解题脚本

#### Go 多方法暴力破解器

```go
// solve_needle.go - 16 线程并发暴力破解
// 支持：Go rand XOR / SubMod / Shuffle / SHA256 哈希 / MD5 哈希
// 详见 solve_needle.go
```

#### Python 分析脚本

```python
from PIL import Image
import numpy as np

img = Image.open('a87ad61f-e3a0-4547-a92c-e7957eaade3c.png')
pixels = np.array(img, dtype=np.uint8)
print(f"Range: {pixels.min()}-{pixels.max()}")  # 0-51
print(f"Shape: {pixels.shape}")  # (150, 150, 3)

# G=51 仅出现 4 次
positions = np.where(pixels[:,:,1] == 51)
for y, x in zip(positions[0], positions[1]):
    print(f"Pixel ({x},{y}): RGB = {tuple(pixels[y,x])}")
```

#### Go 版本像素统计脚本

```go
package main

import (
    "fmt"
    "image/png"
    "os"
)

func main() {
    f, _ := os.Open("a87ad61f-e3a0-4547-a92c-e7957eaade3c.png")
    defer f.Close()
    img, _ := png.Decode(f)

    bounds := img.Bounds()
    min, max := uint32(255), uint32(0)

    for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
        for x := bounds.Min.X; x < bounds.Max.X; x++ {
            r, g, b, _ := img.At(x, y).RGBA()
            // 转为 0-255 范围
            rv, gv, bv := r>>8, g>>8, b>>8
            if rv < min { min = rv }
            if gv < min { min = gv }
            if bv < min { min = bv }
            if rv > max { max = rv }
            if gv > max { max = gv }
            if bv > max { max = bv }
            if gv == 51 {
                fmt.Printf("Pixel (%d,%d): RGB=(%d,%d,%d)\n", x, y, rv, gv, bv)
            }
        }
    }
    fmt.Printf("Range: %d-%d\n", min, max)
}
```

## 使用的工具
- Python (Pillow/numpy) — 像素统计与分析
- Go — 并发暴力搜索
- file — 文件类型与尺寸确认
- zsteg — 可能的 LSB/通道分析（可选）

## 脚本归档
- Go：[`NovruzCTF_one_in_million.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/NovruzCTF_one_in_million.go){target="_blank"}
- Python：[`NovruzCTF_one_in_million.py` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_python/NovruzCTF_one_in_million.py){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 快速检查文件与尺寸
file a87ad61f-e3a0-4547-a92c-e7957eaade3c.png

# 进行 LSB/通道分析（若 zsteg 可用）
zsteg -a a87ad61f-e3a0-4547-a92c-e7957eaade3c.png
```

## 推荐工具与优化解题流程

### 工具对比总结
| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **file** | 文件识别 | <1 分钟 | 快速确认类型 | 仅基础信息 |
| **zsteg** | LSB/通道排查 | ~5 分钟 | 一键扫描 | 对非 LSB 无效 |
| **Python 分析脚本** | 统计特征 | ~5 分钟 | 细节可控 | 需编写脚本 |
| **Go 暴力脚本** | 种子搜索 | 视范围 | 并发快 | 依赖假设正确 |

### 推荐流程
**推荐流程**：file/zsteg 初筛 → Python 统计确认特征 → Go 并发暴力验证 → 未解则转向 C rand / shuffle / hash 分支。

## 未解/进行中说明
- 当前已验证：排除 Python random / numpy / Go rand 的常见编码方式。
- 待补关键结论：真实 PRNG 与像素生成/混淆方式。
- 下一步建议：验证 C/glibc rand、Python shuffle(MT19937)、hash 生成噪声、流密码方案。
