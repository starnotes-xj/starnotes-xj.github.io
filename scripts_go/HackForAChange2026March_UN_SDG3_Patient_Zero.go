// HackForAChange 2026 March - UN SDG3 - Patient Zero (Crypto)
//
// RSA e=3 Stereotyped Message Attack — Go 验证 & 暴力辅助脚本
//
// 说明:
//   Coppersmith 小根攻击的核心 (格基约化 + small_roots) 依赖 SageMath。
//   本 Go 脚本提供:
//     1. 加密参数验证
//     2. 已知 flag 的正确性验证
//     3. 通过 Docker 调用 SageMath 自动求解
//
// 运行:
//   go run HackForAChange2026March_UN_SDG3_Patient_Zero.go

package main

import (
	"fmt"
	"math/big"
	"os/exec"
	"strings"
)

// RSA 参数
var (
	n, _ = new(big.Int).SetString("108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807", 10)
	e    = big.NewInt(3)
	c, _ = new(big.Int).SetString("90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158", 10)

	prefix  = []byte("SDGCTF_SECURE_MSG_V1::")
	suffix  = []byte("::END")
	flagLen = 37
)

// bytesToBigInt 将字节切片转为大整数 (big-endian)
func bytesToBigInt(b []byte) *big.Int {
	return new(big.Int).SetBytes(b)
}

// verifyFlag 验证已知 flag 是否能正确加密为密文 c
func verifyFlag(flag []byte) bool {
	// 构造 padded = prefix || flag || suffix
	padded := make([]byte, 0, len(prefix)+len(flag)+len(suffix))
	padded = append(padded, prefix...)
	padded = append(padded, flag...)
	padded = append(padded, suffix...)

	// m = bytes_to_long(padded)
	m := bytesToBigInt(padded)

	// c_check = m^e mod n
	cCheck := new(big.Int).Exp(m, e, n)

	return cCheck.Cmp(c) == 0
}

// analyzeParams 打印加密参数的关键信息
func analyzeParams() {
	fmt.Println("=== 参数分析 ===")
	fmt.Printf("n 长度: %d bits\n", n.BitLen())
	fmt.Printf("e = %d (极小公钥指数)\n", e)
	fmt.Printf("c 长度: %d bits\n", c.BitLen())
	fmt.Printf("prefix: %q (%d bytes)\n", string(prefix), len(prefix))
	fmt.Printf("suffix: %q (%d bytes)\n", string(suffix), len(suffix))
	fmt.Printf("flag 长度: %d bytes (%d bits)\n", flagLen, flagLen*8)

	totalPadded := len(prefix) + flagLen + len(suffix)
	fmt.Printf("padded 总长度: %d bytes (%d bits)\n", totalPadded, totalPadded*8)
	fmt.Printf("m^3 约 %d bits, n = %d bits → m^3 > n, 发生模约化\n",
		totalPadded*8*3, n.BitLen())

	// n^(1/3) 的近似 bit 长度
	nThirdBits := n.BitLen() / 3
	fmt.Printf("\nCoppersmith 条件: |flag| = 2^%d < n^(1/3) ≈ 2^%d → %s\n",
		flagLen*8, nThirdBits,
		func() string {
			if flagLen*8 < nThirdBits {
				return "满足 ✓"
			}
			return "不满足 ✗"
		}())
	fmt.Printf("余量: %d bits\n", nThirdBits-flagLen*8)
}

// solveSage 通过 Docker 调用 SageMath 求解
func solveSage() (string, error) {
	sageScript := `
n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
e = 3
c = 90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158
prefix = b'SDGCTF_SECURE_MSG_V1::'
suffix = b'::END'
flag_len = 37
P = int.from_bytes(prefix, 'big')
S = int.from_bytes(suffix, 'big')
B = 256^len(suffix)
A = P * 256^(flag_len + len(suffix)) + S
ZmodN = Zmod(n)
PR = PolynomialRing(ZmodN, 'x')
x = PR.gen()
f = (A + B*x)^3 - c
f_monic = f * f.leading_coefficient()^(-1)
roots = f_monic.small_roots(X=2^(flag_len*8), beta=1.0, epsilon=0.02)
for r in roots:
    ri = int(r)
    m = A + B * ri
    if pow(m, 3, n) == c:
        flag = ri.to_bytes(flag_len, 'big')
        print(flag.decode())
`

	cmd := exec.Command("docker", "run", "--rm", "-i",
		"sagemath/sagemath:latest", "bash", "-c",
		"cat > /tmp/solve.sage && sage /tmp/solve.sage")
	cmd.Stdin = strings.NewReader(sageScript)

	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("SageMath 执行失败: %v\n输出: %s", err, string(output))
	}

	result := strings.TrimSpace(string(output))
	return result, nil
}

func main() {
	fmt.Println("╔══════════════════════════════════════════╗")
	fmt.Println("║  Patient Zero — RSA e=3 Coppersmith     ║")
	fmt.Println("╚══════════════════════════════════════════╝")
	fmt.Println()

	// 1. 参数分析
	analyzeParams()
	fmt.Println()

	// 2. 尝试通过 Docker SageMath 求解
	fmt.Println("=== 通过 Docker SageMath 求解 ===")
	flag, err := solveSage()
	if err != nil {
		fmt.Printf("Docker 求解失败: %v\n", err)
		fmt.Println("回退到验证已知 flag...")
		flag = "SDG{3c00bad87b9ba46afa47052e187cec59}"
	} else {
		fmt.Printf("SageMath 求得 flag: %s\n", flag)
	}
	fmt.Println()

	// 3. 验证
	fmt.Println("=== Flag 验证 ===")
	flagBytes := []byte(flag)
	fmt.Printf("Flag: %s\n", flag)
	fmt.Printf("长度: %d bytes\n", len(flagBytes))
	if verifyFlag(flagBytes) {
		fmt.Println("加密验证: PASS ✓")
	} else {
		fmt.Println("加密验证: FAIL ✗")
	}
}
