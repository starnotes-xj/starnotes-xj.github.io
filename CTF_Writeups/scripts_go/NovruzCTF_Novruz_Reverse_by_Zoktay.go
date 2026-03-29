// =============================================================================
// 题目名称: Novruz Reverse by Zoktay
// 题目类别: Reverse Engineering - 静态分析
// 解题思路: 读取二进制文件，检查其中是否包含关键字符串标记（NovruzCT、Masalli、
//
//	xeberdar、2025），若全部存在则直接拼接出 flag
//
// 用法: go run NovruzCTF_Novruz_Reverse_by_Zoktay.go [二进制文件路径]
//
//	示例: go run NovruzCTF_Novruz_Reverse_by_Zoktay.go novruz_rev_zoktay
//
// =============================================================================
package main

import (
	"bytes"
	"fmt"
	"os"
)

const defaultBinaryPath = "novruz_rev_zoktay"

func main() {
	path := defaultBinaryPath
	if len(os.Args) > 1 {
		path = os.Args[1]
	}

	data, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "无法读取文件: %v\n", err)
		os.Exit(1)
	}

	markers := []string{"NovruzCT", "Masalli", "xeberdar", "2025"}
	missing := false
	for _, m := range markers {
		if !bytes.Contains(data, []byte(m)) {
			fmt.Fprintf(os.Stderr, "未发现关键标记: %s\n", m)
			missing = true
		}
	}
	if missing {
		os.Exit(1)
	}

	flag := "NovruzCTF{21_Masalli_xeberdar2025}"
	fmt.Println(flag)
}
