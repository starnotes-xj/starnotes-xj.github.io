// =============================================================================
// 题目名称: Pakhlivan fell in love with Zoktay (Crack Me)
// 题目类别: Reverse - RC4 解密
// 解题思路: 二进制中使用 RC4 加密，密钥为 "this_is_not_flag"，
//
//	提取密文后用 RC4 解密即可还原 flag
//
// 用法: go run NovruzCTF_Pakhlivan_fell_in_love_with_Zoktay.go
// =============================================================================
package main

import "fmt"

// rc4KSA 执行 RC4 密钥调度算法（Key Scheduling Algorithm）
func rc4KSA(key []byte) []byte {
	S := make([]byte, 256)
	for i := 0; i < 256; i++ {
		S[i] = byte(i)
	}
	j := 0
	for i := 0; i < 256; i++ {
		j = (j + int(S[i]) + int(key[i%len(key)])) & 0xff
		S[i], S[j] = S[j], S[i]
	}
	return S
}

// rc4PRGA 执行 RC4 伪随机生成算法（Pseudo-Random Generation Algorithm）
func rc4PRGA(S []byte, data []byte) []byte {
	i, j := 0, 0
	out := make([]byte, len(data))
	for idx, b := range data {
		i = (i + 1) & 0xff
		j = (j + int(S[i])) & 0xff
		S[i], S[j] = S[j], S[i]
		k := S[(int(S[i])+int(S[j]))&0xff]
		out[idx] = b ^ k
	}
	return out
}

func main() {
	key := []byte("this_is_not_flag")
	cipher := []byte{
		0x65, 0xf9, 0x45, 0xce, 0x8a, 0x60, 0xe0, 0x90,
		0xfe, 0x66, 0xff, 0x67, 0xef, 0x1b, 0xd1, 0x2e,
		0xf1, 0x6b, 0xa4, 0x0f, 0x96, 0x9e, 0xbe, 0xc0,
		0x0b, 0x88, 0xc3, 0x40, 0x06, 0x27, 0x5a, 0xd2,
		0xdf, 0xa6, 0x15, 0x0d, 0x8d, 0xef, 0xcf, 0x29,
		0x83, 0xa4, 0x44, 0x3d, 0xd7, 0x9b, 0xf4, 0x9e,
		0x87, 0x67, 0x4d, 0xcf, 0x4e, 0x5a, 0xe0, 0x6b,
		0xf4, 0x13, 0xe1, 0xdc, 0xbb, 0xce, 0x73, 0x14,
		0xee, 0x09, 0xe3, 0x4f, 0x46,
	}

	S := rc4KSA(key)
	plain := rc4PRGA(S, cipher)
	text := string(plain)
	// 二进制中 flag 前缀为 "Cup{"，替换为正确的 CTF 前缀
	if len(text) >= 4 && text[:4] == "Cup{" {
		text = "novruzCTF{" + text[4:]
	}
	fmt.Println(text)
}
