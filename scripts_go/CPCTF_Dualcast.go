package main

import (
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
)

// extractDecimalValue 从 `c = 12345` 这样的文本中提取十进制整数部分。
func extractDecimalValue(text string) (*big.Int, error) {
	re := regexp.MustCompile(`c\s*=\s*(\d+)`)
	matches := re.FindStringSubmatch(text)
	if len(matches) != 2 {
		return nil, fmt.Errorf("未在 out.txt 中找到形如 `c = <整数>` 的输出")
	}

	value := new(big.Int)
	if _, ok := value.SetString(matches[1], 10); !ok {
		return nil, fmt.Errorf("无法解析十进制整数: %s", matches[1])
	}
	return value, nil
}

func main() {
	_, currentFile, _, ok := runtime.Caller(0)
	if !ok {
		panic("无法定位当前脚本路径")
	}

	// 当前文件位于 CTF_Writeups/scripts_go，向上一层回到 CTF_Writeups 根目录。
	baseDir := filepath.Dir(filepath.Dir(currentFile))
	outPath := filepath.Join(baseDir, "files", "Dualcast", "out.txt")

	rawText, err := os.ReadFile(outPath)
	if err != nil {
		panic(err)
	}

	c, err := extractDecimalValue(string(rawText))
	if err != nil {
		panic(err)
	}

	// big.Int.Bytes() 返回无符号大端序字节切片，正好对应 bytes_to_long 的逆过程。
	fmt.Println(string(c.Bytes()))
}
