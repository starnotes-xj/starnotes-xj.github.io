// HackForAChange 2026 March - UN SDG3 - Encrypted Audit Logs (Crypto)
//
// XOR 重复密钥加密 + 已知明文攻击
//
// 攻击思路:
//   1. 审计日志中第 108 行的 Base32 token 解码后为非 ASCII — 被 XOR 加密
//   2. 日志第 62 行泄露: XOR mode=repeating key_len=4
//   3. Flag 格式 "SDG{" 恰好 4 字节, 已知明文攻击恢复密钥
//
// 运行: go run HackForAChange2026March_UN_SDG3_Encrypted_Audit_Logs.go

package main

import (
	"encoding/base32"
	"fmt"
)

func main() {
	fmt.Println("========================================")
	fmt.Println("Encrypted Audit Logs — XOR KPA Attack")
	fmt.Println("========================================")

	// 第 108 行的加密 token (Base32)
	encryptedB32 := "LHHPPHR25OEII2F22XIG7OWS2IZ3FVWTNS7YTAB65DJNKPV42XKW72EH2R3Q===="

	// Step 1: Base32 解码
	ciphertext, err := base32.StdEncoding.DecodeString(encryptedB32)
	if err != nil {
		fmt.Printf("Base32 解码失败: %v\n", err)
		return
	}
	fmt.Printf("\n[Step 1] Base32 解码\n")
	fmt.Printf("  密文 hex: %x\n", ciphertext)
	fmt.Printf("  密文长度: %d bytes\n", len(ciphertext))

	// Step 2: 已知明文攻击恢复密钥
	// 日志第 62 行: XOR mode=repeating key_len=4
	// Flag 格式 "SDG{" = 4 字节 = key_len
	knownPT := []byte("SDG{")
	key := make([]byte, 4)
	for i := 0; i < 4; i++ {
		key[i] = ciphertext[i] ^ knownPT[i]
	}
	fmt.Printf("\n[Step 2] 已知明文攻击\n")
	fmt.Printf("  已知明文: %s\n", string(knownPT))
	fmt.Printf("  恢复密钥: 0x%x\n", key)

	// Step 3: XOR 解密
	plaintext := make([]byte, len(ciphertext))
	for i := range ciphertext {
		plaintext[i] = ciphertext[i] ^ key[i%4]
	}
	flag := string(plaintext)
	fmt.Printf("\n[Step 3] XOR 解密\n")
	fmt.Printf("  Flag: %s\n", flag)

	// 验证
	if len(flag) > 4 && flag[:4] == "SDG{" && flag[len(flag)-1] == '}' {
		fmt.Println("  格式验证: PASS")
	} else {
		fmt.Println("  格式验证: FAIL")
	}
}
