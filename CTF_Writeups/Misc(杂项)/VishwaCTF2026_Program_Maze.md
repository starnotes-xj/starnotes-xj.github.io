# VishwaCTF 2026 - 程序迷宫 (Program Maze) Writeup

## 题目信息
- **比赛**: VishwaCTF 2026
- **题目**: 程序迷宫 (Program Maze)
- **类别**: Misc
- **难度**: 中等
- **附件/URL**: 启动容器后访问获取迷宫文件
- **附件链接**: [下载附件](https://starnotes-xj.github.io/BIGC_CTF_Writeups/files/Program_Maze/maze_output.txt){download} · [仓库位置](https://github.com/starnotes-xj/BIGC_CTF_Writeups/tree/main/CTF_Writeups/files/Program_Maze){target="_blank"}
- **Flag格式**: `VishwaCTF{}`
- **状态**: 已解

## Flag

```text
VishwaCTF{p4th_1s_th3_m3ss4g3_00_ea67138d}
```

## 解题过程

### 1. 初始侦察/文件识别
- 入口点：启动容器后访问服务，获取一个纯文本迷宫文件
- 文件头部包含关键元信息：
  ```
  # LABYRINTH MAP FILE  //  CLASSIFIED
  # Dims      : 51 x 701
  # Entry     : col=0,    row=1      [ marked > ]
  # Exit      : col=50,   row=699    [ marked < ]
  # HINT: The map is just the canvas.
  #       The true message is the journey you take to escape it.
  ```
- 迷宫使用 `#` 表示墙壁、`.` 表示通道，入口标记 `>`，出口标记 `<`
- 关键提示："地图只是画布，真正的信息是你逃出迷宫的旅程" —— 说明 flag 编码在**解迷宫的路径**中

### 2. 关键突破点一 —— BFS 求解最短路径
- 迷宫尺寸 51x701，人工不可能走通，必须编程求解
- 使用 BFS（广度优先搜索）从入口 `(row=1, col=0)` 搜索到出口 `(row=699, col=50)`
- 求解得到路径长度 1093 步
- 提取路径方向序列：`R`(右)、`L`(左)、`D`(下)、`U`(上)
- 统计：R=222、L=172、D=698、U=0（路径整体自上而下蛇形前进，从不回头向上）

### 3. 关键突破点二 —— 从转弯方向中提取二进制信息
- 路径的主体运动方向是向下（D），在每个通道转角处向左或向右偏移一列
- 提取所有"从向下转为水平"的转弯方向（即每次 `D` 后紧跟的 `L` 或 `R`），共 345 个转弯决策
- 将转弯方向编码为二进制：**L=1, R=0**
- 每 8 位一组转换为 ASCII 字符

### 4. 获取 Flag
- 345 个转弯方向按 L=1、R=0 编码后，8-bit 分组解码得到：
  ```
  VishwaCTF{p4th_1s_th3_m3ss4g3_00_ea67138d}
  ```
- flag 含义："path is the message"（路径即消息），与提示完美呼应

## 攻击链/解题流程总结

```text
读取迷宫文件 → BFS 求解最短路径 → 提取每次向下后的 L/R 转弯方向 → L=1,R=0 二进制编码 → 8-bit ASCII 解码 → Flag
```

## 漏洞分析 / 机制分析

### 根因
- 迷宫路径在每个转弯点嵌入了 1 bit 信息（左转=1，右转=0），利用迷宫的唯一解路径作为信息载体
- 这是一种**隐写术（Steganography）**：将信息隐藏在迷宫路径的几何形状中

### 影响
- 迷宫看起来是普通的随机迷宫，但路径的每个转弯方向都经过精心设计来编码消息
- 不解迷宫就无法获取信息，增加了信息提取的门槛

### 修复建议（适用于漏洞类题目）
- 本题非漏洞类，为隐写术/编程挑战题目，不需要修复建议

## 知识点
- **BFS（广度优先搜索）**：图论中求解无权图最短路径的经典算法，适用于迷宫求解
- **路径隐写术**：将二进制信息嵌入迷宫路径的方向选择中，每个转弯点编码 1 bit
- **二进制到 ASCII 转换**：8 位二进制分组解码为可读字符
- **迷宫数据结构**：使用二维字符网格表示，`#` 为墙壁、`.` 为通道

## 使用的工具
- Go — 编写 BFS 迷宫求解器并解码路径信息
- 文本编辑器 — 分析迷宫文件头部元信息和提示

## 脚本归档
- Go：[`VishwaCTF2026_Program_Maze.go` :material-open-in-new:](https://github.com/starnotes-xj/BIGC_CTF_Writeups/blob/main/CTF_Writeups/scripts_go/VishwaCTF2026_Program_Maze.go){target="_blank"}

## 命令行提取关键数据（无 GUI）

```bash
# 启动容器后获取迷宫文件
curl http://<container-url> > maze_output.txt

# 运行解题脚本
go run VishwaCTF2026_Program_Maze.go
```

## 推荐工具与优化解题流程

### 工具对比总结

| 工具 | 适用阶段 | 本题耗时 | 优点 | 缺点 |
|------|----------|----------|------|------|
| **Go 脚本** | BFS + 解码 | < 1 秒 | 性能优异、编译型语言处理大迷宫快 | 需手写 BFS |
| **Python 脚本** | BFS + 解码 | 1-2 秒 | 代码简洁、collections.deque 方便 | 大迷宫可能较慢 |

### 推荐流程

**推荐流程**：分析文件头提示 → 编写 BFS 求解器 → 分析方向序列编码 → 尝试多种二进制映射 → Flag（10-15 分钟）。

### Go 脚本（推荐首选）
- **安装**：Go 1.18+
- **详细步骤**：
  1. 解析迷宫文件，跳过注释行，构建二维网格
  2. BFS 从 `>` 搜索到 `<`，记录父节点用于回溯路径
  3. 提取路径方向序列，筛选"D 后紧跟 L/R"的转弯点
  4. L=1, R=0 编码，8-bit 分组转 ASCII
- **优势**：执行速度快，适合处理 51x701 的大迷宫
