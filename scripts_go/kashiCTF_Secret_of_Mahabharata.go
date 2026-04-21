package main

// kashiCTF - Secret of Mahabharata
// 题目描述：秘密信息每隔64年重新加密（Base64编码），历经3136年
// 解题思路：3136 ÷ 64 = 49 次 Base64 编码，循环解码即可还原明文
// Flag: kashiCTF{th3_s3cr3t_0f_mah4bh4r4t4_fr0m_3136_BCE}

import (
	"encoding/base64"
	"fmt"
	"os"
)

func main() {
	// 读取被多次 Base64 编码的密文文件
	data, err := os.ReadFile("secret_message.txt")
	if err != nil {
		panic(err)
	}

	// 循环解码：每次尝试 Base64 解码，失败则说明已到达明文
	for i := 1; ; i++ {
		decoded, err := base64.StdEncoding.DecodeString(string(data))
		if err != nil {
			// 无法继续解码 → 当前 data 即为最终明文
			fmt.Printf("共解码 %d 次\n", i-1)
			fmt.Printf("Flag: %s\n", string(data))
			break
		}
		data = decoded
		fmt.Printf("第 %d 次解码完成, 剩余大小: %d bytes\n", i, len(data))
	}

	// 注意：原始 flag 格式为 flag{...}，需手动替换为 kashiCTF{...}
}
