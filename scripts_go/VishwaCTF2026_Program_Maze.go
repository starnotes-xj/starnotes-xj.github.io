package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// Point 表示迷宫中的坐标 (行, 列)
type Point struct{ r, c int }

func main() {
	// 读取迷宫文件
	f, err := os.Open("maze_output.txt")
	if err != nil {
		fmt.Println("无法打开文件:", err)
		return
	}
	defer f.Close()

	// 解析迷宫：跳过 "# " 开头的注释行，保留实际迷宫数据
	var maze []string
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 1024*1024), 1024*1024)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "# ") {
			continue
		}
		maze = append(maze, line)
	}
	fmt.Printf("迷宫大小: %d 行 x %d 列\n", len(maze), len(maze[0]))

	// 定位入口 '>' 和出口 '<'
	var entry, exit Point
	for r, row := range maze {
		for c, ch := range row {
			if ch == '>' {
				entry = Point{r, c}
			}
			if ch == '<' {
				exit = Point{r, c}
			}
		}
	}
	fmt.Printf("入口: (%d, %d), 出口: (%d, %d)\n", entry.r, entry.c, exit.r, exit.c)

	// 判断坐标是否可通行（'.', '>', '<' 均可通行）
	isPassable := func(r, c int) bool {
		if r < 0 || r >= len(maze) || c < 0 || c >= len(maze[r]) {
			return false
		}
		ch := maze[r][c]
		return ch == '.' || ch == '>' || ch == '<'
	}

	// BFS（广度优先搜索）求解最短路径
	queue := []Point{entry}
	parent := map[Point]Point{entry: {-1, -1}} // 记录每个节点的父节点，用于回溯路径
	dirs := []Point{{0, 1}, {0, -1}, {1, 0}, {-1, 0}} // 右、左、下、上

	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		if cur == exit {
			break
		}
		for _, d := range dirs {
			np := Point{cur.r + d.r, cur.c + d.c}
			if isPassable(np.r, np.c) {
				if _, visited := parent[np]; !visited {
					parent[np] = cur
					queue = append(queue, np)
				}
			}
		}
	}

	// 回溯重建完整路径（从出口到入口，再翻转）
	var path []Point
	pos := exit
	sentinel := Point{-1, -1}
	for pos != sentinel {
		path = append(path, pos)
		pos = parent[pos]
	}
	for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
		path[i], path[j] = path[j], path[i]
	}
	fmt.Printf("路径长度: %d 步\n", len(path))

	// 提取路径方向序列
	var directions []byte
	for i := 1; i < len(path); i++ {
		dr := path[i].r - path[i-1].r
		dc := path[i].c - path[i-1].c
		switch {
		case dc == 1:
			directions = append(directions, 'R') // 向右
		case dc == -1:
			directions = append(directions, 'L') // 向左
		case dr == 1:
			directions = append(directions, 'D') // 向下
		case dr == -1:
			directions = append(directions, 'U') // 向上
		}
	}

	// 提取关键信息：每次从"向下(D)"转为"水平(L/R)"时的方向
	// 这些转弯点编码了隐藏的二进制信息
	var turnDirs []byte
	for i := 1; i < len(directions); i++ {
		if directions[i-1] == 'D' && (directions[i] == 'L' || directions[i] == 'R') {
			turnDirs = append(turnDirs, directions[i])
		}
	}
	fmt.Printf("转弯决策点: %d 个\n", len(turnDirs))

	// 解码：L=1, R=0，每 8 位一组转换为 ASCII 字符
	fmt.Print("解码结果: ")
	for i := 0; i+8 <= len(turnDirs); i += 8 {
		val := 0
		for j := 0; j < 8; j++ {
			val <<= 1
			if turnDirs[i+j] == 'L' {
				val |= 1 // L 编码为 1
			}
			// R 编码为 0，不需要额外操作
		}
		fmt.Printf("%c", val)
	}
	fmt.Println()
}
