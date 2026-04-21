// kashiCTF 2026 - Broadcast
// Hastad 广播攻击：e=3，三份密文完全相同，说明 m^3 = c（无模约减）
// 直接对密文 c 计算整数立方根即可恢复明文

package main

import (
	"fmt"
	"math/big"
)

func main() {
	// 三份密文完全相同，取任意一份
	c := new(big.Int)
	c.SetString("475436441896018898725156479190091126537849994697426945980826369000641892902004477923335055269088235139492237640527487698088281484953901383579636883543216552932099156009006828723690550706326538736801225046068870773990108130474408522838234755277972911893744937243892927414355347438993698991261629557719442242861719577879055371620865465785392597257968132649494474946507819896785671106833645551504301840437212737125", 10)

	// 二分法求整数立方根
	// 目标：找到 m 使得 m^3 = c
	lo := big.NewInt(0)
	hi := new(big.Int).Set(c)
	one := big.NewInt(1)
	two := big.NewInt(2)
	three := big.NewInt(3)

	for lo.Cmp(hi) < 0 {
		// mid = (lo + hi + 1) / 2
		mid := new(big.Int).Add(lo, hi)
		mid.Add(mid, one)
		mid.Div(mid, two)

		// 计算 mid^3
		cube := new(big.Int).Exp(mid, three, nil)
		if cube.Cmp(c) <= 0 {
			lo.Set(mid) // mid^3 <= c，往右搜索
		} else {
			hi.Sub(mid, one) // mid^3 > c，往左搜索
		}
	}

	// 验证 lo^3 == c
	cube := new(big.Int).Exp(lo, three, nil)
	if cube.Cmp(c) != 0 {
		fmt.Println("错误：c 不是完全立方数，需要使用 CRT 方法")
		return
	}

	// 将大整数转为字节后解码为 ASCII 字符串
	flag := string(lo.Bytes())
	fmt.Println("Flag:", flag)
}
