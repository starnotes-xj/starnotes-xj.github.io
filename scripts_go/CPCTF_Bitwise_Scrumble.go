package main

import (
	"fmt"
	"math/big"
	"strconv"
)

// CPCTF - Bitwise Scrumble
//
// 附件把 flag 转成 75 位十进制整数串后分成 3 个 25 位块。
// 每一位十进制数字都会和对应 key 数字做看似不同的 bitwise 表达式。
// 根据真值表可化简出三种表达式都等价于 digit ^ key_digit，
// 因此解密时再异或同一个 key_digit 即可还原原十进制数字。

const (
	key = "0123456789012109876543210"
	enc = "10aa77170b38758c146245779086332e5e8237430f362d317310124333b999b890043152135"
)

func recoverDecimalDigits(part string) string {
	result := make([]byte, 0, len(part))
	for i := 0; i < len(part); i++ {
		keyDigit, err := strconv.Atoi(string(key[i]))
		if err != nil {
			panic(err)
		}
		encryptedNibble, err := strconv.ParseInt(string(part[i]), 16, 64)
		if err != nil {
			panic(err)
		}
		result = append(result, byte(int(encryptedNibble)^keyDigit)+'0')
	}
	return string(result)
}

func main() {
	firstPart := enc[:25]
	secondPart := enc[25:50]
	thirdPart := enc[50:75]

	decimalText := recoverDecimalDigits(firstPart) +
		recoverDecimalDigits(secondPart) +
		recoverDecimalDigits(thirdPart)

	flagNumber := new(big.Int)
	if _, ok := flagNumber.SetString(decimalText, 10); !ok {
		panic("failed to parse recovered decimal text")
	}

	fmt.Println(string(flagNumber.Bytes()))
}
