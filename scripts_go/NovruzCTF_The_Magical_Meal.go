package main

import (
	"fmt"
	"math/big"
	"math/rand"
	"os"
	"time"
)

// ======================== 参数 ========================
// 从图片中读取的 ElGamal 参数
var (
	pStr  = "1905671816403772611477075447515791022372594380344434356222414517909417652709503859707116441682578631751"
	gStr  = "35184372088891"
	hStr  = "51604037746295575257434694992797642501681250360811180981081060940424101015886204338530685374507425988​2"
	c1Str = "13251053023241332020308632831721495676720694896334569119269980510533474438817146321474966159216834357​10"
	c2Str = "11056527390041988343879110954122996897662668728642448446777690219172267373214290325892278730831161042​28"
)

// ======================== 工具函数 ========================

func bigFromStr(s string) *big.Int {
	// 清除可能的不可见字符（如零宽空格）
	clean := ""
	for _, c := range s {
		if c >= '0' && c <= '9' {
			clean += string(c)
		}
	}
	n := new(big.Int)
	n.SetString(clean, 10)
	return n
}

// pollardRho 使用 Pollard's rho 算法分解 n
func pollardRho(n *big.Int) *big.Int {
	if new(big.Int).Mod(n, big.NewInt(2)).Sign() == 0 {
		return big.NewInt(2)
	}

	rng := rand.New(rand.NewSource(time.Now().UnixNano()))
	one := big.NewInt(1)

	for {
		c := new(big.Int).Rand(rng, new(big.Int).Sub(n, big.NewInt(2)))
		c.Add(c, one)
		x := new(big.Int).Rand(rng, new(big.Int).Sub(n, big.NewInt(2)))
		x.Add(x, one)
		y := new(big.Int).Set(x)
		d := big.NewInt(1)

		f := func(v *big.Int) *big.Int {
			r := new(big.Int).Mul(v, v)
			r.Add(r, c)
			r.Mod(r, n)
			return r
		}

		for d.Cmp(one) == 0 {
			x = f(x)
			y = f(f(y))
			diff := new(big.Int).Sub(x, y)
			diff.Abs(diff)
			d.GCD(nil, nil, diff, n)
		}

		if d.Cmp(n) != 0 {
			return d
		}
	}
}

// factorize 完全分解 n，返回 {素因子: 指数} 映射
func factorize(n *big.Int) map[string]int {
	factors := make(map[string]int)
	if n.Cmp(big.NewInt(1)) <= 0 {
		return factors
	}

	remaining := new(big.Int).Set(n)

	// 试除法，小素数
	smallPrimes := make([]int64, 0, 1000)
	sieve := make([]bool, 10_000_000)
	for i := 2; i < len(sieve); i++ {
		if !sieve[i] {
			smallPrimes = append(smallPrimes, int64(i))
			for j := i * i; j < len(sieve); j += i {
				sieve[j] = true
			}
		}
	}

	for _, sp := range smallPrimes {
		p := big.NewInt(sp)
		for {
			mod := new(big.Int).Mod(remaining, p)
			if mod.Sign() == 0 {
				factors[p.String()]++
				remaining.Div(remaining, p)
			} else {
				break
			}
		}
	}

	// Pollard's rho 处理剩余部分
	var factorRecursive func(n *big.Int)
	factorRecursive = func(n *big.Int) {
		if n.Cmp(big.NewInt(1)) <= 0 {
			return
		}
		if n.ProbablyPrime(25) {
			factors[n.String()]++
			return
		}
		d := pollardRho(n)
		factorRecursive(d)
		factorRecursive(new(big.Int).Div(n, d))
	}

	if remaining.Cmp(big.NewInt(1)) > 0 {
		factorRecursive(remaining)
	}

	return factors
}

// babyStepGiantStep 在 Z_p* 的阶为 order 的子群中求离散对数
// 找 x 使得 g^x = h (mod p)，0 <= x < order
func babyStepGiantStep(g, h, p, order *big.Int) *big.Int {
	// m = ceil(sqrt(order))
	m := new(big.Int).Sqrt(order)
	m.Add(m, big.NewInt(1))

	// Baby step: 建表 {g^j mod p : j} for j in [0, m)
	table := make(map[string]*big.Int)
	gj := big.NewInt(1) // g^0
	for j := big.NewInt(0); j.Cmp(m) < 0; j.Add(j, big.NewInt(1)) {
		table[gj.String()] = new(big.Int).Set(j)
		gj = new(big.Int).Mul(gj, g)
		gj.Mod(gj, p)
	}

	// Giant step: g^(-m) mod p
	gm := new(big.Int).Exp(g, m, p)
	gmInv := new(big.Int).ModInverse(gm, p)

	// 搜索: h * (g^(-m))^i for i in [0, m)
	gamma := new(big.Int).Set(h)
	for i := big.NewInt(0); i.Cmp(m) < 0; i.Add(i, big.NewInt(1)) {
		if j, ok := table[gamma.String()]; ok {
			// x = i*m + j
			x := new(big.Int).Mul(i, m)
			x.Add(x, j)
			x.Mod(x, order)
			return x
		}
		gamma.Mul(gamma, gmInv)
		gamma.Mod(gamma, p)
	}

	return nil // 未找到
}

// pohligHellman 使用 Pohlig-Hellman 算法求 g^x = h (mod p)
// 其中 g 的阶整除 groupOrder，factors 是 groupOrder 的素因子分解
func pohligHellman(g, h, p, groupOrder *big.Int, factors map[string]int) *big.Int {
	residues := make([]*big.Int, 0)
	moduli := make([]*big.Int, 0)

	for qStr, e := range factors {
		q := bigFromStr(qStr)
		qe := new(big.Int).Exp(q, big.NewInt(int64(e)), nil) // q^e

		// g' = g^(order/q^e) mod p
		exp := new(big.Int).Div(groupOrder, qe)
		gPrime := new(big.Int).Exp(g, exp, p)
		hPrime := new(big.Int).Exp(h, exp, p)

		fmt.Printf("  子群 q=%s, e=%d, q^e=%s ... ", qStr, e, qe.String())

		if e == 1 {
			// 简单情况：直接 BSGS
			xi := babyStepGiantStep(gPrime, hPrime, p, q)
			if xi == nil {
				fmt.Println("BSGS 失败!")
				continue
			}
			fmt.Printf("x_%s = %s\n", qStr, xi.String())
			residues = append(residues, xi)
			moduli = append(moduli, new(big.Int).Set(qe))
		} else {
			// q^e > 1 的情况，逐位提取
			// x mod q^e = x0 + x1*q + x2*q^2 + ...
			gBase := new(big.Int).Exp(g, new(big.Int).Div(groupOrder, q), p) // g^(order/q)
			xi := big.NewInt(0)
			gInvXi := big.NewInt(1) // g^(-xi) 的累积

			for k := 0; k < e; k++ {
				// h_k = (h * g^(-xi))^(order/q^(k+1))
				qk1 := new(big.Int).Exp(q, big.NewInt(int64(k+1)), nil)
				expK := new(big.Int).Div(groupOrder, qk1)

				hg := new(big.Int).Mul(h, gInvXi)
				hg.Mod(hg, p)
				hk := new(big.Int).Exp(hg, expK, p)

				// BSGS: gBase^dk = hk
				dk := babyStepGiantStep(gBase, hk, p, q)
				if dk == nil {
					dk = big.NewInt(0)
				}

				// xi += dk * q^k
				qkVal := new(big.Int).Exp(q, big.NewInt(int64(k)), nil)
				term := new(big.Int).Mul(dk, qkVal)
				xi.Add(xi, term)

				// 更新 g^(-xi)
				gInvXi = new(big.Int).Exp(g, new(big.Int).Neg(xi), nil)
				gInvXi.Mod(gInvXi, p)
				if gInvXi.Sign() < 0 {
					gInvXi.Add(gInvXi, p)
				}
				// 更准确的做法
				gXi := new(big.Int).Exp(g, xi, p)
				gInvXi = new(big.Int).ModInverse(gXi, p)
			}

			fmt.Printf("x mod %s = %s\n", qe.String(), xi.String())
			residues = append(residues, xi)
			moduli = append(moduli, new(big.Int).Set(qe))
		}
	}

	// CRT 合并
	return crt(residues, moduli)
}

// crt 中国剩余定理
func crt(residues, moduli []*big.Int) *big.Int {
	if len(residues) == 0 {
		return big.NewInt(0)
	}

	// M = 所有模数的乘积
	M := big.NewInt(1)
	for _, m := range moduli {
		M.Mul(M, m)
	}

	result := big.NewInt(0)
	for i := range residues {
		Mi := new(big.Int).Div(M, moduli[i])
		yi := new(big.Int).ModInverse(Mi, moduli[i])
		if yi == nil {
			continue
		}
		term := new(big.Int).Mul(residues[i], Mi)
		term.Mul(term, yi)
		result.Add(result, term)
	}

	result.Mod(result, M)
	return result
}

func main() {
	p := bigFromStr(pStr)
	g := bigFromStr(gStr)
	h := bigFromStr(hStr)
	c1 := bigFromStr(c1Str)
	c2 := bigFromStr(c2Str)

	fmt.Printf("p  = %s\n", p.String())
	fmt.Printf("g  = %s\n", g.String())
	fmt.Printf("h  = %s\n", h.String())
	fmt.Printf("c1 = %s\n", c1.String())
	fmt.Printf("c2 = %s\n", c2.String())
	fmt.Printf("p 位数: %d, 比特: %d\n", len(p.String()), p.BitLen())
	fmt.Printf("p 是素数: %v\n\n", p.ProbablyPrime(25))

	// Step 1: 分解 p-1
	fmt.Println("=== Step 1: 分解 p-1 ===")
	pMinus1 := new(big.Int).Sub(p, big.NewInt(1))
	fmt.Printf("p-1 = %s\n", pMinus1.String())

	start := time.Now()
	factors := factorize(pMinus1)
	fmt.Printf("分解耗时: %v\n", time.Since(start))
	fmt.Printf("p-1 的素因子分解:\n")

	// 验证分解
	check := big.NewInt(1)
	for qStr, e := range factors {
		q := bigFromStr(qStr)
		qe := new(big.Int).Exp(q, big.NewInt(int64(e)), nil)
		check.Mul(check, qe)
		fmt.Printf("  %s ^ %d\n", qStr, e)
	}
	fmt.Printf("分解验证: %v\n\n", check.Cmp(pMinus1) == 0)

	// 检查最大因子
	maxFactor := big.NewInt(0)
	for qStr := range factors {
		q := bigFromStr(qStr)
		if q.Cmp(maxFactor) > 0 {
			maxFactor.Set(q)
		}
	}
	fmt.Printf("最大素因子: %s (%d bits)\n\n", maxFactor.String(), maxFactor.BitLen())

	if maxFactor.BitLen() > 40 {
		fmt.Println("警告: 最大素因子较大，BSGS 可能较慢")
	}

	// Step 2: Pohlig-Hellman 求离散对数
	fmt.Println("=== Step 2: Pohlig-Hellman 求离散对数 ===")
	start = time.Now()
	x := pohligHellman(g, h, p, pMinus1, factors)
	fmt.Printf("求解耗时: %v\n", time.Since(start))
	fmt.Printf("私钥 x = %s\n\n", x.String())

	// 验证: g^x mod p == h?
	hCheck := new(big.Int).Exp(g, x, p)
	fmt.Printf("验证 g^x mod p == h: %v\n\n", hCheck.Cmp(h) == 0)

	if hCheck.Cmp(h) != 0 {
		fmt.Println("错误: 离散对数验证失败!")
		os.Exit(1)
	}

	// Step 3: ElGamal 解密
	fmt.Println("=== Step 3: ElGamal 解密 ===")
	// s = c1^x mod p
	s := new(big.Int).Exp(c1, x, p)
	// s_inv = s^(-1) mod p
	sInv := new(big.Int).ModInverse(s, p)
	// m = c2 * s_inv mod p
	m := new(big.Int).Mul(c2, sInv)
	m.Mod(m, p)

	fmt.Printf("明文 m = %s\n\n", m.String())

	// 转换为字节/字符串
	mBytes := m.Bytes()
	fmt.Printf("十六进制: %x\n", mBytes)
	fmt.Printf("文本: %s\n", string(mBytes))
}
