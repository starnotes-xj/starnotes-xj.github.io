package main

import (
	"fmt"
	"math/big"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
)

// CPCTF - 1、0、7
//
// 这份 Go 脚本复现与 Python 版完全相同的利用链：
// 1. 从归档附件中读取 N、e、c；
// 2. 识别 N 的十进制结构是否为 1^k 0^t 7^k；
// 3. 构造 p = (10^k - 1) / 9 与 q = 10^(t+k) + 7；
// 4. 计算 d = e^(-1) mod phi 并还原明文。

var paramPattern = regexp.MustCompile(`(?m)^(N|e|c)=(\d+)\r?$`)
var structurePattern = regexp.MustCompile(`^(1+)(0+)(7+)$`)

func attachmentPath() string {
	_, currentFile, _, ok := runtime.Caller(0)
	if !ok {
		panic("无法定位当前脚本路径")
	}

	// 当前文件位于 CTF_Writeups/scripts_go，向上一层回到 CTF_Writeups 根目录。
	baseDir := filepath.Dir(filepath.Dir(currentFile))
	return filepath.Join(baseDir, "files", "1、0、7", "107107_b38e4b4bcd49c22b496049abb867695331cdc0f7542dd59288b3597e1b8e4119.txt")
}

func parseParameters(text string) (map[string]*big.Int, error) {
	matches := paramPattern.FindAllStringSubmatch(text, -1)
	values := make(map[string]*big.Int, 3)

	for _, match := range matches {
		value := new(big.Int)
		if _, ok := value.SetString(match[2], 10); !ok {
			return nil, fmt.Errorf("无法解析十进制整数: %s", match[2])
		}
		values[match[1]] = value
	}

	for _, key := range []string{"N", "e", "c"} {
		if _, ok := values[key]; !ok {
			return nil, fmt.Errorf("附件中缺少参数: %s", key)
		}
	}

	return values, nil
}

func deriveFactors(modulus *big.Int) (*big.Int, *big.Int, error) {
	match := structurePattern.FindStringSubmatch(modulus.String())
	if len(match) != 4 {
		return nil, nil, fmt.Errorf("N 的十进制结构不是 1^k 0^t 7^k")
	}

	ones := match[1]
	zeros := match[2]
	sevens := match[3]

	if len(ones) != len(sevens) {
		return nil, nil, fmt.Errorf("N 首尾块长度不一致")
	}

	k := int64(len(ones))
	shift := int64(len(zeros) + len(sevens))

	ten := big.NewInt(10)
	nine := big.NewInt(9)
	one := big.NewInt(1)
	seven := big.NewInt(7)

	// p = (10^k - 1) / 9 = 111...111
	p := new(big.Int).Exp(ten, big.NewInt(k), nil)
	p.Sub(p, one)
	p.Div(p, nine)

	// q = 10^(t+k) + 7
	q := new(big.Int).Exp(ten, big.NewInt(shift), nil)
	q.Add(q, seven)

	check := new(big.Int).Mul(new(big.Int).Set(p), new(big.Int).Set(q))
	if check.Cmp(modulus) != 0 {
		return nil, nil, fmt.Errorf("按结构推导出的 p、q 无法还原 N")
	}

	return p, q, nil
}

func main() {
	rawText, err := os.ReadFile(attachmentPath())
	if err != nil {
		panic(err)
	}

	params, err := parseParameters(string(rawText))
	if err != nil {
		panic(err)
	}

	n := params["N"]
	e := params["e"]
	c := params["c"]

	p, q, err := deriveFactors(n)
	if err != nil {
		panic(err)
	}

	one := big.NewInt(1)
	phi := new(big.Int).Mul(
		new(big.Int).Sub(new(big.Int).Set(p), one),
		new(big.Int).Sub(new(big.Int).Set(q), one),
	)

	d := new(big.Int).ModInverse(e, phi)
	if d == nil {
		panic("无法求出 e 在 phi 下的逆元")
	}

	m := new(big.Int).Exp(c, d, n)
	fmt.Println(string(m.Bytes()))
}
