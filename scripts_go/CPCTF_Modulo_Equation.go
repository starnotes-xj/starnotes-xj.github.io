package main

import "fmt"

func main() {
	// 读入题目给定的 A、B。约束保证 1 <= B < A <= 300。
	var a, b int
	fmt.Scanln(&a, &b)

	// 题目已经明确保证：
	// 1. 一定存在满足条件的正整数 x
	// 2. 其中最小解不超过 10^5
	// 因此最稳妥的做法就是从 1 开始顺次枚举，遇到第一个满足
	// x % A == B % x 的解立刻输出。
	for x := 1; ; x++ {
		if x%a == b%x {
			fmt.Println(x)
			return
		}
	}
}
