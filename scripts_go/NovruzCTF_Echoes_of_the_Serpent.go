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

func main() {
	var knownMACHex string
	var oracleMACHex string
	fmt.Scanln(&knownMACHex)
	fmt.Scanln(&oracleMACHex)
	knownMAC, _ := hex.DecodeString(knownMACHex)
	oracleMAC, _ := hex.DecodeString(oracleMACHex)

	// pad("hello_world") = "hello_world" + 5 个零字节（补齐到 16 字节块）
	helloPadded := zero_pad([]byte("hello_world"))

	// pad("get_flag") = "get_flag" + 8 个零字节（补齐到 16 字节块）
	getflagPadded := zero_pad([]byte("get_flag"))

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
func zero_pad(data []byte) []byte {
	if len(data)%16 != 0 {
		return append(data, make([]byte, 16-len(data)%16)...)
	}
	return data
}
