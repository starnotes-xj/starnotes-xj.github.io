package main

import (
	"flag"
	"fmt"
	"math/big"
	"regexp"
)

// ACSC Qualification 2026 - Dino Vault
//
// 离线求解脚本：输入同一只恐龙（例如 Vexillum Rex）在同一连接中
// 两次下载得到的密文与模数，利用共享素因子攻击恢复明文。
//
// 关键判断 RSA 的依据：
//   1. n = p * q（两个大素数相乘）
//   2. e = 2^16 + 1 = 65537
//   3. c = m^e mod n
//
// 运行示例：
// go run CTF_Writeups/scripts_go/ACSC2026Qualification_Dino_Vault.go \
//   -ciphertext1 <hex1> -modulus1 <n1> \
//   -ciphertext2 <hex2> -modulus2 <n2>

const publicExponent int64 = 65537

var dnaLookup = map[byte]int64{
	'A': 0,
	'T': 1,
	'G': 2,
	'C': 3,
}

func mustParseHex(name, raw string) *big.Int {
	value, ok := new(big.Int).SetString(raw, 16)
	if !ok {
		panic(fmt.Sprintf("invalid hex for %s", name))
	}
	return value
}

func mustParseDec(name, raw string) *big.Int {
	value, ok := new(big.Int).SetString(raw, 10)
	if !ok {
		panic(fmt.Sprintf("invalid decimal for %s", name))
	}
	return value
}

func mustInverseModulo(e, phi *big.Int) *big.Int {
	inverse := new(big.Int).ModInverse(e, phi)
	if inverse == nil {
		panic("modular inverse does not exist")
	}
	return inverse
}

func fromDNA(dna string) string {
	if len(dna)%4 != 0 {
		panic("dna length is not a multiple of 4")
	}

	plaintext := make([]byte, 0, len(dna)/4)
	for i := 0; i < len(dna); i += 4 {
		var value int64
		for j := 0; j < 4; j++ {
			base := dna[i+j]
			decoded, ok := dnaLookup[base]
			if !ok {
				panic(fmt.Sprintf("unexpected DNA base %q", base))
			}
			value |= decoded << (2 * j)
		}
		plaintext = append(plaintext, byte(value))
	}
	return string(plaintext)
}

func extractFlag(plaintext string) string {
	re := regexp.MustCompile(`dach2026\{[^}]+\}`)
	return re.FindString(plaintext)
}

func main() {
	ciphertext1Raw := flag.String("ciphertext1", "", "first ciphertext in hex")
	modulus1Raw := flag.String("modulus1", "", "first modulus in decimal")
	ciphertext2Raw := flag.String("ciphertext2", "", "second ciphertext in hex")
	modulus2Raw := flag.String("modulus2", "", "second modulus in decimal")
	flag.Parse()

	if *ciphertext1Raw == "" || *modulus1Raw == "" || *ciphertext2Raw == "" || *modulus2Raw == "" {
		flag.Usage()
		panic("all four inputs are required")
	}

	c1 := mustParseHex("ciphertext1", *ciphertext1Raw)
	n1 := mustParseDec("modulus1", *modulus1Raw)
	n2 := mustParseDec("modulus2", *modulus2Raw)

	sharedPrime := new(big.Int).GCD(nil, nil, n1, n2)
	if sharedPrime.Cmp(big.NewInt(1)) == 0 || sharedPrime.Cmp(n1) == 0 || sharedPrime.Cmp(n2) == 0 {
		panic("no useful shared prime found; ensure both pairs come from the same dino in one connection")
	}

	q1 := new(big.Int).Quo(new(big.Int).Set(n1), sharedPrime)
	phi := new(big.Int).Mul(
		new(big.Int).Sub(new(big.Int).Set(sharedPrime), big.NewInt(1)),
		new(big.Int).Sub(new(big.Int).Set(q1), big.NewInt(1)),
	)

	e := big.NewInt(publicExponent)
	d := mustInverseModulo(e, phi)

	messageInt := new(big.Int).Exp(c1, d, n1)
	dna := string(messageInt.Bytes())
	plaintext := fromDNA(dna)
	flagValue := extractFlag(plaintext)

	fmt.Printf("[+] shared prime bits: %d\n", sharedPrime.BitLen())
	fmt.Printf("[+] shared prime: %s\n", sharedPrime.String())
	fmt.Printf("[+] recovered plaintext: %s\n", plaintext)
	if flagValue != "" {
		fmt.Printf("[+] flag: %s\n", flagValue)
	} else {
		fmt.Println("[!] no dach2026{...} flag pattern found; inspect recovered plaintext manually")
	}
}
