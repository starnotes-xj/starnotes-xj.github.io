package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
)

// CPCTF - Sign up for traP
//
// 判定输入字符串是否满足：
// 1. 长度 1..32；
// 2. 仅包含 A-Z / a-z / 0-9 / _ / -；
// 3. 首尾不是 _ 或 -。
//
// 正则含义：
// ^[A-Za-z0-9]                         首字符必须是字母或数字
// (?:[A-Za-z0-9_-]{0,30}[A-Za-z0-9])?  可选的中间与尾字符：总长度扩展到 2..32，尾字符仍是字母或数字
// $                                    匹配到字符串结尾
var traQIDPattern = regexp.MustCompile(`^[A-Za-z0-9](?:[A-Za-z0-9_-]{0,30}[A-Za-z0-9])?$`)

func main() {
	reader := bufio.NewReader(os.Stdin)
	var s string
	fmt.Fscan(reader, &s)

	if traQIDPattern.MatchString(s) {
		fmt.Println(200)
	} else {
		fmt.Println(400)
	}
}
