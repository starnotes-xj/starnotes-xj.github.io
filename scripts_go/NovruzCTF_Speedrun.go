package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"net"
	"os"
	"regexp"
	"strconv"
	"strings"
	"time"
)

var opMap map[byte]string
var rulesRe = regexp.MustCompile(`'(.)'\s*=>\s*(\w+)`)

var rulesTag = []byte("RULES:")
var calcTag = []byte("Calculate: ")
var protoTag = []byte("PROTOCOL UPDATE")

func main() {
	addr := "142.93.12.237:1337"
	if len(os.Args) > 1 {
		addr = os.Args[1]
	}

	fmt.Printf("[*] Connecting to %s...\n", addr)
	start := time.Now()

	conn, err := net.DialTimeout("tcp", addr, 10*time.Second)
	if err != nil {
		fmt.Println("[-] Failed:", err)
		os.Exit(1)
	}
	defer conn.Close()

	if tc, ok := conn.(*net.TCPConn); ok {
		_ = tc.SetNoDelay(true)
		_ = tc.SetReadBuffer(1 << 20)
		_ = tc.SetWriteBuffer(1 << 20)
		_ = tc.SetKeepAlive(true)
		_ = tc.SetKeepAlivePeriod(5 * time.Second)
	}

	fmt.Printf("[*] Connected in %v\n", time.Since(start))

	opMap = make(map[byte]string)
	solved := 0
	answerBuf := make([]byte, 0, 8192)

	reader := bufio.NewReaderSize(conn, 1<<20)
	for {
		line, err := reader.ReadBytes('\n')
		if len(line) == 0 && err != nil {
			if err == io.EOF {
				break
			}
			fmt.Fprintln(os.Stderr, "read error:", err)
			break
		}

		line = bytes.TrimSpace(line)
		if len(line) == 0 {
			if err != nil && err != io.EOF {
				break
			}
			continue
		}

		if bytes.Contains(line, rulesTag) {
			parseRules(string(line))
			continue
		}

		if calcIdx := bytes.Index(line, calcTag); calcIdx >= 0 {
			expr := bytes.TrimSpace(line[calcIdx+len(calcTag):])
			result := evaluate(string(expr))
			answerBuf = strconv.AppendInt(answerBuf[:0], result, 10)
			answerBuf = append(answerBuf, '\n')
			_, _ = conn.Write(answerBuf)
			solved++
			if solved%64 == 0 {
				fmt.Fprintf(os.Stderr, "[*] %d/256 at %v\n", solved, time.Since(start))
			}
			continue
		}

		if len(line) > 0 && !bytes.HasPrefix(line, []byte("####")) && !bytes.Contains(line, protoTag) {
			fmt.Println(string(line))
		}

		if err == io.EOF {
			break
		}
	}

	elapsed := time.Since(start)
	fmt.Printf("\n[*] Solved: %d/256 in %v (%.1fms/round)\n", solved, elapsed, float64(elapsed.Milliseconds())/float64(max(solved, 1)))
}

func parseRules(line string) {
	opMap = make(map[byte]string)
	for _, m := range rulesRe.FindAllStringSubmatch(line, -1) {
		opMap[m[1][0]] = strings.ToUpper(m[2])
	}
}

func evaluate(expr string) int64 {
	pos := 0
	return parseExpr(expr, &pos)
}

func parseExpr(expr string, pos *int) int64 {
	for *pos < len(expr) && expr[*pos] == ' ' {
		*pos++
	}
	if *pos >= len(expr) {
		return 0
	}

	if expr[*pos] == '(' {
		*pos++
		left := parseExpr(expr, pos)
		for *pos < len(expr) && expr[*pos] == ' ' {
			*pos++
		}
		if *pos < len(expr) && expr[*pos] == ')' {
			*pos++
			return left
		}
		op := expr[*pos]
		*pos++
		right := parseExpr(expr, pos)
		for *pos < len(expr) && expr[*pos] == ' ' {
			*pos++
		}
		if *pos < len(expr) && expr[*pos] == ')' {
			*pos++
		}
		return applyOp(op, left, right)
	}

	start := *pos
	if *pos < len(expr) && (expr[*pos] == '-' || expr[*pos] == '+') {
		*pos++
	}
	for *pos < len(expr) && expr[*pos] >= '0' && expr[*pos] <= '9' {
		*pos++
	}
	if start == *pos {
		return 0
	}
	n, _ := strconv.ParseInt(expr[start:*pos], 10, 64)
	return n
}

func applyOp(sym byte, a, b int64) int64 {
	opName, ok := opMap[sym]
	if !ok {
		switch sym {
		case '+':
			return a + b
		case '-':
			return a - b
		case '*':
			return a * b
		case '/':
			if b == 0 {
				return 0
			}
			return a / b
		case '%':
			if b == 0 {
				return 0
			}
			return pythonMod(a, b)
		case '^':
			return a ^ b
		case '&':
			return a & b
		case '|':
			return a | b
		}
		return 0
	}

	switch opName {
	case "ADD":
		return a + b
	case "SUB":
		return a - b
	case "MUL":
		return a * b
	case "DIV":
		if b == 0 {
			return 0
		}
		return pythonDiv(a, b)
	case "MOD":
		if b == 0 {
			return 0
		}
		return pythonMod(a, b)
	case "XOR":
		return a ^ b
	case "AND":
		return a & b
	case "OR":
		return a | b
	case "LSHIFT":
		if b < 0 || b > 63 {
			return 0
		}
		return a << uint(b)
	case "RSHIFT":
		if b < 0 || b > 63 {
			return 0
		}
		return a >> uint(b)
	case "POW":
		return intPow(a, b)
	}
	return 0
}

func pythonMod(a, b int64) int64 {
	r := a % b
	if r != 0 && (r < 0) != (b < 0) {
		r += b
	}
	return r
}

func pythonDiv(a, b int64) int64 {
	r := a / b
	if (a^b) < 0 && r*b != a {
		r--
	}
	return r
}

func intPow(base, exp int64) int64 {
	if exp < 0 {
		return 0
	}
	result := int64(1)
	for exp > 0 {
		if exp%2 == 1 {
			result *= base
		}
		exp /= 2
		base *= base
	}
	return result
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
