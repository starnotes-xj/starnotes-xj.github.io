package main

import "fmt"

const (
	// LCG 递推参数：state_{n+1} = (A * state_n + C) mod 2^32
	lcgMultiplier uint32 = 1664525
	lcgIncrement  uint32 = 1013904223

	// 题目只泄露高 16 位，因此右移 16 位即得到输出
	outputShiftBits = 16

	// 目标位置：需要预测 position 100 的输出
	targetStep = 100
)

// 题目给出的连续输出（position 0-3）
var observedOutputs = [...]uint16{52338, 24512, 16929, 35379}

// 计算 LCG 的下一状态（uint32 溢出等价于 mod 2^32）
func nextState(state uint32) uint32 {
	return lcgMultiplier*state + lcgIncrement
}

// 将状态推进指定步数
func advanceState(state uint32, steps int) uint32 {
	for i := 0; i < steps; i++ {
		state = nextState(state)
	}
	return state
}

// 验证候选 state0 是否与已知输出序列一致
func matchesObservedOutputs(initialState uint32) bool {
	state := initialState
	for _, expected := range observedOutputs[1:] {
		state = nextState(state)
		if uint16(state>>outputShiftBits) != expected {
			return false
		}
	}
	return true
}

// 枚举 state0 的低 16 位，筛选出唯一可行的候选状态
func candidateStates() []uint32 {
	firstOutput := observedOutputs[0]
	var candidates []uint32

	for lowBits := uint32(0); lowBits < 1<<outputShiftBits; lowBits++ {
		// state0 的高 16 位来自 output0，低 16 位枚举
		state := (uint32(firstOutput) << outputShiftBits) | lowBits
		if matchesObservedOutputs(state) {
			candidates = append(candidates, state)
		}
	}

	return candidates
}

func main() {
	candidates := candidateStates()
	if len(candidates) != 1 {
		fmt.Printf("candidate states: %v\n", candidates)
		return
	}

	state0 := candidates[0]
	state100 := advanceState(state0, targetStep)

	// 打印唯一的 state0 与位置 100 的输出
	fmt.Printf("state0 = %d 0x%08x\n", state0, state0)
	fmt.Printf("output_100 = %d\n", state100>>outputShiftBits)
}
