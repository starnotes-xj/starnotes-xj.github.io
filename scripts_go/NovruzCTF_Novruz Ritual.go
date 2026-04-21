// =============================================================================
// 题目名称: Novruz Ritual
// 题目类别: Reverse - 静态分析
// 解题思路: 二进制中包含三个阶段的检查（水/火/风），每个阶段通过简单的
//
//	数学运算和字符重排生成密码片段，静态还原即可得到 flag
//
// 用法: go run NovruzCTF_Novruz Ritual.go
// =============================================================================
package main

import "fmt"

func main() {
	// stageWater: 目标值减去密钥，再按索引重排
	target := []int{0x79, 0x64, 0x68, 0x76}
	key := []int{5, 2, 7, 1}
	idx := []int{2, 0, 3, 1}
	water := make([]byte, 4)
	for i := 0; i < 4; i++ {
		water[idx[i]] = byte(target[i] - key[i])
	}

	// stageFire: 直接给出的 ASCII 值
	b0 := 116
	b1 := 111
	b2 := 110
	b3 := 113
	fire := string([]byte{byte(b0), byte(b1), byte(b2), byte(b3)})

	// stageWind: 注意 w2 和 w3 的顺序是交换的
	w0 := 107
	w1 := 111
	w3 := 97
	w2 := 115
	wind := string([]byte{byte(w0), byte(w1), byte(w2), byte(w3)})

	phrase := fmt.Sprintf("%s-%s-%s", string(water), fire, wind)
	fmt.Printf("novruzCTF{%s}\n", phrase)
}
