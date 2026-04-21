// =============================================================================
// 题目名称: Novruz Reverse by Zoktay (radare2 版)
// 题目类别: Reverse Engineering - radare2 动态分析
// 解题思路: 使用 radare2 反汇编 xor_decrypt 函数，从指令中提取 XOR key，
//
//	验证 key 为 0x42 后输出 flag
//
// 依赖: radare2 (r2)
// 用法: go run NovruzCTF_Novruz_Reverse_by_Zoktay_r2.go [二进制文件路径]
//
//	示例: go run NovruzCTF_Novruz_Reverse_by_Zoktay_r2.go novruz_rev_zoktay
//
// =============================================================================
package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strings"
)

const defaultBinaryPathR2 = "novruz_rev_zoktay"

func runR2(path string, cmd string) (string, error) {
	c := exec.Command("r2", "-q", "-c", cmd, path)
	out, err := c.CombinedOutput()
	return string(out), err
}

func main() {
	path := defaultBinaryPathR2
	if len(os.Args) > 1 {
		path = os.Args[1]
	}

	if _, err := exec.LookPath("r2"); err != nil {
		fmt.Fprintln(os.Stderr, "未找到 radare2 (r2)，请先安装。")
		os.Exit(1)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		fmt.Fprintf(os.Stderr, "无法读取文件: %v\n", err)
		os.Exit(1)
	}

	markers := []string{"NovruzCT", "Masalli", "xeberdar", "2025"}
	for _, m := range markers {
		if !bytes.Contains(data, []byte(m)) {
			fmt.Fprintf(os.Stderr, "未发现关键标记: %s\n", m)
		}
	}

	out, err := runR2(path, "aaa; pdf @ sym._Z11xor_decryptPcPKcmc")
	if err != nil {
		fmt.Fprintf(os.Stderr, "radare2 执行失败: %v\n", err)
		os.Exit(1)
	}

	re := regexp.MustCompile(`xor\s+al,\s*0x([0-9a-fA-F]{1,2})`)
	m := re.FindStringSubmatch(out)
	key := ""
	if len(m) == 2 {
		key = strings.ToLower(m[1])
	}

	if key == "42" {
		fmt.Println("检测到 XOR key = 0x42")
		fmt.Println("NovruzCTF{21_Masalli_xeberdar2025}")
		return
	}

	fmt.Println("未能从 xor_decrypt 反汇编中解析到 key，请手动查看：")
	fmt.Println(out)
}
