// =============================================================================
// 题目名称: XOR 42
// 题目类别: PPC - 数学表达式构造
// 解题思路: 服务器给定整数 a，要求仅用 +、-、*、/ 和常量构造表达式使结果等于
//
//	a XOR 42。利用 IEEE 754 双精度浮点的 banker's rounding 技巧
//	(加减 6755399441055744) 实现逐位异或运算
//
// 用法: go run NovruzCTF_Floating_in_Samani.go [目标地址]
//
//	示例: go run NovruzCTF_Floating_in_Samani.go tcp.canyouhack.org:10091
//
// =============================================================================
package main

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

const defaultXORAddr = "tcp.canyouhack.org:10091"

// buildPayload 构造等价于 a XOR 42 的纯算术表达式
// 利用 IEEE 754 双精度浮点的 banker's rounding 技巧提取各个二进制位
func buildPayload() string {
	return "a + 42" +
		" - 4 * (a / 2 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
		" + 8 * (a / 4 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
		" - 16 * (a / 8 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
		" + 32 * (a / 16 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
		" - 64 * (a / 32 - 63 / 128 + 6755399441055744 - 6755399441055744)" +
		" + 128 * (a / 64 - 63 / 128 + 6755399441055744 - 6755399441055744)"
}

func main() {
	addr := defaultXORAddr
	if len(os.Args) > 1 {
		addr = os.Args[1]
	}

	conn, err := net.DialTimeout("tcp", addr, 10*time.Second)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[!] 连接失败: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	_ = conn.SetDeadline(time.Now().Add(10 * time.Second))
	reader := bufio.NewReader(conn)

	// 读取服务器提示符
	_ = conn.SetReadDeadline(time.Now().Add(2 * time.Second))
	_, _ = reader.ReadBytes('>')
	_ = conn.SetReadDeadline(time.Time{})

	// 发送 payload
	payload := buildPayload()
	fmt.Fprintf(conn, "%s\n", payload)

	// 读取服务器响应
	_ = conn.SetReadDeadline(time.Now().Add(5 * time.Second))
	resp, _ := io.ReadAll(reader)
	if len(resp) > 0 {
		fmt.Print(string(resp))
	}
}
