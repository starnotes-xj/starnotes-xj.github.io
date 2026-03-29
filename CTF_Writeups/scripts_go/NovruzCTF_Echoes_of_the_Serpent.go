// =============================================================================
// 题目名称: Echoes of the Serpent
// 题目类别: Crypto - CBC-MAC 长度扩展攻击
// 解题思路: 已知 MAC("hello_world") 和 oracle 返回的 MAC 值，利用 CBC-MAC
//
//	长度扩展特性构造伪造消息: pad("hello_world") || (MAC XOR pad("get_flag"))，
//	使其 MAC 值等于 oracle 提供的值
//
// 用法: go run NovruzCTF_Echoes_of_the_Serpent.go
// =============================================================================
package main

import (
	"encoding/hex"
	"fmt"
)

const (
	// MAC("hello_world") 的已知值
	knownMACHex = "77ec0fdf191b1011b974864b443a60ad"
	// oracle 返回的目标 MAC 值
	oracleMACHex = "162cb90b16adeb0dcdc9776c3af7b324"
)

func main() {
	knownMAC, _ := hex.DecodeString(knownMACHex)
	oracleMAC, _ := hex.DecodeString(oracleMACHex)

	// pad("hello_world") = "hello_world" + 5 个零字节（补齐到 16 字节块）
	helloPadded := append([]byte("hello_world"), make([]byte, 5)...)

	// pad("get_flag") = "get_flag" + 8 个零字节（补齐到 16 字节块）
	getflagPadded := append([]byte("get_flag"), make([]byte, 8)...)

	// 构造第二个块: block2 = MAC(hello_world) XOR pad(get_flag)
	block2 := make([]byte, 16)
	for i := range block2 {
		block2[i] = knownMAC[i] ^ getflagPadded[i]
	}

	// 伪造消息 = pad("hello_world") || block2
	forgedMsg := append(helloPadded, block2...)

	fmt.Println("Prophecy (hex):", hex.EncodeToString(forgedMsg))
	fmt.Println("Seal (hex):", hex.EncodeToString(oracleMAC))
}
