// =============================================================================
// 题目名称: Ancient Spell (SSTV)
// 题目类别: Misc - 摩尔斯电码解码
// 解题思路: 音频中使用 "bi"=点 "bo"=划 的自定义编码表示摩尔斯电码，
//
//	解码后得到明文字符串
//
// 用法: echo "bi bo bibo" | go run NovruzCTF_WYCGPRB.go
//
//	cat morse_input.txt | go run NovruzCTF_WYCGPRB.go
//
// =============================================================================
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// morseMap 标准摩尔斯电码映射表
var morseMap = map[string]string{
	".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
	"..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
	"-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
	".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
	"..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
	"--..": "Z", "-----": "0", ".----": "1", "..---": "2", "...--": "3",
	"....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8",
	"----.": "9",
}

// decodeWord 将 bi/bo 编码的单词转换为摩尔斯电码再解码
// bi = 点(.)，bo = 划(-)
func decodeWord(w string) string {
	parts := []string{}
	for i := 0; i < len(w); {
		if strings.HasPrefix(w[i:], "bi") {
			parts = append(parts, ".")
			i += 2
			continue
		}
		if strings.HasPrefix(w[i:], "bo") {
			parts = append(parts, "-")
			i += 2
			continue
		}
		i++
	}
	morse := strings.Join(parts, "")
	if v, ok := morseMap[morse]; ok {
		return v
	}
	return "?"
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	for in.Scan() {
		line := strings.TrimSpace(in.Text())
		if line == "" {
			continue
		}
		words := strings.Fields(line)
		out := strings.Builder{}
		for _, w := range words {
			out.WriteString(decodeWord(w))
		}
		fmt.Println(out.String())
	}
}
