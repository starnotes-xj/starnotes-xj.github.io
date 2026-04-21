package main

import (
	"bufio"
	"bytes"
	"flag"
	"fmt"
	"math/bits"
	"net"
	"regexp"
	"sort"
	"strings"
	"time"
)

// CPCTF - Ultra Janken Tournament
//
// 这份 Go 版脚本与 Python 版保持同一条利用链：
// 1. 把 server.py 里的 nextrand 视为 GF(2) 上的 64 维线性变换；
// 2. 用它的一个 64 次消去多项式构造合法 luck pattern 线性码；
// 3. 通过自定义 strategy 让 codeword 对应的低 8 个 message bit 直接编码 winner；
// 4. 每一轮对公开的 120 bit luck pattern 做最近码字 beam search，再批量发送 C/index/G。

const (
	host        = "133.88.122.244"
	port        = 32035
	strategyLen = 120
	prompt      = "What will you do? [C]heat the luck / [G]o Janken!: "
)

var (
	// 对应精确版 nextrand() 的一个消去多项式：
	// x^64 + x^51 + x^49 + x^48 + x^46 + x^45 + x^43 + x^42 + x^41 + x^39
	// + x^38 + x^35 + x^34 + x^33 + x^32 + x^31 + x^30 + x^23 + x^21 + x^20
	// + x^17 + x^16 + x^14 + x^13 + x^10 + x^8 + x^4 + x^3 + x^2 + 1
	taps = []int{
		0, 2, 3, 4, 8, 10, 13, 14, 16, 17, 20, 21, 23,
		30, 31, 32, 33, 34, 35, 38, 39, 41, 42, 43, 45,
		46, 48, 49, 51, 64,
	}

	targetPattern = regexp.MustCompile(`Your Number is No: (\d+)`)
	luckPattern   = regexp.MustCompile(`Current Luck Pattern: ([01]{120})`)
	flagPattern   = regexp.MustCompile(`(CPCTF\{[^\r\n]+\}|FLAG\{[^\r\n]+\})`)
)

// BitMask 用两个 uint64 表示 120 bit：
// - Lo 保存 bit 0..63
// - Hi 保存 bit 64..119（只用低 56 bit）
type BitMask struct {
	Lo uint64
	Hi uint64
}

func (m BitMask) xor(other BitMask) BitMask {
	return BitMask{
		Lo: m.Lo ^ other.Lo,
		Hi: m.Hi ^ other.Hi,
	}
}

func (m BitMask) and(other BitMask) BitMask {
	return BitMask{
		Lo: m.Lo & other.Lo,
		Hi: m.Hi & other.Hi,
	}
}

func (m BitMask) or(other BitMask) BitMask {
	return BitMask{
		Lo: m.Lo | other.Lo,
		Hi: m.Hi | other.Hi,
	}
}

func (m BitMask) popCount() int {
	return bits.OnesCount64(m.Lo) + bits.OnesCount64(m.Hi)
}

func (m BitMask) bitAt(index int) bool {
	if index < 64 {
		return ((m.Lo >> index) & 1) == 1
	}
	return ((m.Hi >> (index - 64)) & 1) == 1
}

func setBit(mask *BitMask, index int) {
	if index < 64 {
		mask.Lo |= 1 << index
		return
	}
	mask.Hi |= 1 << (index - 64)
}

func maskFromBits(bitsText string) (BitMask, error) {
	var out BitMask
	if len(bitsText) != strategyLen {
		return out, fmt.Errorf("luck pattern 长度异常: %d", len(bitsText))
	}

	for idx, ch := range bitsText {
		switch ch {
		case '0':
			// nothing
		case '1':
			setBit(&out, idx)
		default:
			return out, fmt.Errorf("luck pattern 含非法字符: %q", ch)
		}
	}
	return out, nil
}

type solverContext struct {
	playerStrategy []uint64
	varMasks       []BitMask
	frozenMasks    []BitMask
	constCache     []BitMask
}

func buildPlayerStrategy() []uint64 {
	// 反解前 8 个 codeword bit 对应的低 8 个 message bit 线性关系。
	messageMasks := make([]uint8, 8)
	for i := 0; i < 8; i++ {
		mask := uint8(1 << i)
		for _, tap := range taps[1:] {
			if tap <= i {
				mask ^= messageMasks[i-tap]
			}
		}
		messageMasks[i] = mask
	}

	strategy := make([]uint64, strategyLen)
	for codewordBit := 0; codewordBit < 8; codewordBit++ {
		var value uint64
		for messageBit, mask := range messageMasks {
			if ((mask >> codewordBit) & 1) == 1 {
				value |= 1 << messageBit
			}
		}
		strategy[codewordBit] = value
	}
	return strategy
}

func buildSolverContext() solverContext {
	playerStrategy := buildPlayerStrategy()

	freePositions := make([]int, 0, 48)
	for position := 55; position >= 8; position-- {
		freePositions = append(freePositions, position)
	}

	varMasks := make([]BitMask, 0, len(freePositions))
	for _, position := range freePositions {
		var mask BitMask
		for _, tap := range taps {
			bitIndex := position + tap
			if bitIndex < strategyLen {
				setBit(&mask, bitIndex)
			}
		}
		varMasks = append(varMasks, mask)
	}

	futureUnion := make([]BitMask, len(varMasks)+1)
	var running BitMask
	for idx := len(varMasks) - 1; idx >= 0; idx-- {
		running = running.or(varMasks[idx])
		futureUnion[idx] = running
	}

	allBits := BitMask{
		Lo: ^uint64(0),
		Hi: (uint64(1) << 56) - 1,
	}

	frozenMasks := make([]BitMask, len(varMasks)+1)
	for idx := range frozenMasks {
		frozenMasks[idx] = allBits.xor(futureUnion[idx])
	}

	constCache := make([]BitMask, 256)
	for value := 0; value < 256; value++ {
		var mask BitMask
		for bit := 0; bit < 8; bit++ {
			if ((value >> bit) & 1) == 0 {
				continue
			}
			for _, tap := range taps {
				bitIndex := bit + tap
				if bitIndex < strategyLen {
					if mask.bitAt(bitIndex) {
						// toggle
						if bitIndex < 64 {
							mask.Lo ^= 1 << bitIndex
						} else {
							mask.Hi ^= 1 << (bitIndex - 64)
						}
					} else {
						setBit(&mask, bitIndex)
					}
				}
			}
		}
		constCache[value] = mask
	}

	return solverContext{
		playerStrategy: playerStrategy,
		varMasks:       varMasks,
		frozenMasks:    frozenMasks,
		constCache:     constCache,
	}
}

type beamState struct {
	mask  BitMask
	score int
}

func solvePattern(bitsText string, target int, ctx solverContext, width int) (int, []int, error) {
	receivedMask, err := maskFromBits(bitsText)
	if err != nil {
		return 0, nil, err
	}

	bestDistance := int(^uint(0) >> 1)
	bestMask := BitMask{}
	bestValue := 0

	for _, value := range []int{target, target + 101, target + 202} {
		if value >= 256 {
			continue
		}

		currentStates := map[BitMask]int{
			ctx.constCache[value]: ctx.constCache[value].xor(receivedMask).and(ctx.frozenMasks[0]).popCount(),
		}

		for depth, variableMask := range ctx.varMasks {
			frozenMask := ctx.frozenMasks[depth+1]
			nextStates := make(map[BitMask]int, len(currentStates)*2)

			for partialMask := range currentStates {
				score0 := partialMask.xor(receivedMask).and(frozenMask).popCount()
				if previous, ok := nextStates[partialMask]; !ok || score0 < previous {
					nextStates[partialMask] = score0
				}

				partialWithVariable := partialMask.xor(variableMask)
				score1 := partialWithVariable.xor(receivedMask).and(frozenMask).popCount()
				if previous, ok := nextStates[partialWithVariable]; !ok || score1 < previous {
					nextStates[partialWithVariable] = score1
				}
			}

			if len(nextStates) > width {
				items := make([]beamState, 0, len(nextStates))
				for mask, score := range nextStates {
					items = append(items, beamState{mask: mask, score: score})
				}
				sort.Slice(items, func(i, j int) bool {
					if items[i].score != items[j].score {
						return items[i].score < items[j].score
					}
					if items[i].mask.Hi != items[j].mask.Hi {
						return items[i].mask.Hi < items[j].mask.Hi
					}
					return items[i].mask.Lo < items[j].mask.Lo
				})

				pruned := make(map[BitMask]int, width)
				for idx := 0; idx < width; idx++ {
					pruned[items[idx].mask] = items[idx].score
				}
				currentStates = pruned
			} else {
				currentStates = nextStates
			}
		}

		for candidateMask := range currentStates {
			distance := candidateMask.xor(receivedMask).popCount()
			if distance < bestDistance {
				bestDistance = distance
				bestMask = candidateMask
				bestValue = value
			}
		}
	}

	flips := make([]int, 0, bestDistance)
	for idx, ch := range bitsText {
		expected := byte('0')
		if bestMask.bitAt(idx) {
			expected = '1'
		}
		if byte(ch) != expected {
			flips = append(flips, idx)
		}
	}

	return bestValue, flips, nil
}

type remote struct {
	conn   net.Conn
	reader *bufio.Reader
	buffer []byte
}

func newRemote(host string, port int) (*remote, error) {
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 30*time.Second)
	if err != nil {
		return nil, err
	}
	if err := conn.SetReadDeadline(time.Time{}); err != nil {
		conn.Close()
		return nil, err
	}
	return &remote{
		conn:   conn,
		reader: bufio.NewReader(conn),
		buffer: make([]byte, 0, 4096),
	}, nil
}

func (r *remote) recvUntil(marker string) (string, error) {
	target := []byte(marker)
	for !bytes.Contains(r.buffer, target) {
		if err := r.conn.SetReadDeadline(time.Now().Add(120 * time.Second)); err != nil {
			return "", err
		}
		chunk := make([]byte, 65536)
		n, err := r.reader.Read(chunk)
		if n > 0 {
			r.buffer = append(r.buffer, chunk[:n]...)
		}
		if err != nil {
			return "", err
		}
	}

	idx := bytes.Index(r.buffer, target) + len(target)
	out := string(r.buffer[:idx])
	r.buffer = append([]byte(nil), r.buffer[idx:]...)
	return out, nil
}

func (r *remote) recvAll() (string, error) {
	var out bytes.Buffer
	out.Write(r.buffer)
	r.buffer = nil

	for {
		if err := r.conn.SetReadDeadline(time.Now().Add(5 * time.Second)); err != nil {
			return "", err
		}

		chunk := make([]byte, 65536)
		n, err := r.reader.Read(chunk)
		if n > 0 {
			out.Write(chunk[:n])
		}
		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				break
			}
			break
		}
	}

	return out.String(), nil
}

func (r *remote) send(data string) error {
	_, err := r.conn.Write([]byte(data))
	return err
}

func (r *remote) close() error {
	return r.conn.Close()
}

func solveRemote(host string, port int, width int, verbose bool) (string, error) {
	ctx := buildSolverContext()

	r, err := newRemote(host, port)
	if err != nil {
		return "", err
	}
	defer r.close()

	if _, err = r.recvUntil("Your Strategy: "); err != nil {
		return "", err
	}

	var strategyBuilder strings.Builder
	for idx, value := range ctx.playerStrategy {
		if idx > 0 {
			strategyBuilder.WriteByte(' ')
		}
		fmt.Fprintf(&strategyBuilder, "%d", value)
	}
	strategyBuilder.WriteByte('\n')
	if err = r.send(strategyBuilder.String()); err != nil {
		return "", err
	}

	block, err := r.recvUntil(prompt)
	if err != nil {
		return "", err
	}

	totalFlips := 0
	for round := 0; round < 20; round++ {
		targetMatch := targetPattern.FindStringSubmatch(block)
		luckMatch := luckPattern.FindStringSubmatch(block)
		if len(targetMatch) != 2 || len(luckMatch) != 2 {
			return "", fmt.Errorf("无法解析第 %d 轮的 player_no / luck pattern", round+1)
		}

		var target int
		if _, err = fmt.Sscanf(targetMatch[1], "%d", &target); err != nil {
			return "", fmt.Errorf("无法解析目标编号: %w", err)
		}

		chosenValue, flips, err := solvePattern(luckMatch[1], target, ctx, width)
		if err != nil {
			return "", err
		}
		totalFlips += len(flips)

		if verbose {
			fmt.Printf(
				"round %d: target=%d chosen=%d flips=%d total=%d\n",
				round+1,
				target,
				chosenValue,
				len(flips),
				totalFlips,
			)
		}

		var payload strings.Builder
		for _, idx := range flips {
			fmt.Fprintf(&payload, "C\n%d\n", idx)
		}
		payload.WriteString("G\n")
		if err = r.send(payload.String()); err != nil {
			return "", err
		}

		// 每个 C/index 对会触发一次相同 prompt。
		for range flips {
			if _, err = r.recvUntil(prompt); err != nil {
				return "", err
			}
		}

		if round != 19 {
			block, err = r.recvUntil(prompt)
			if err != nil {
				return "", err
			}
		}
	}

	trailer, err := r.recvAll()
	if err != nil {
		return "", err
	}

	flagMatch := flagPattern.FindStringSubmatch(trailer)
	if len(flagMatch) != 2 {
		return "", fmt.Errorf("20 轮结束后未找到 flag")
	}
	return flagMatch[1], nil
}

func main() {
	hostFlag := flag.String("host", host, "challenge host")
	portFlag := flag.Int("port", port, "challenge port")
	widthFlag := flag.Int("width", 1000, "beam width")
	quietFlag := flag.Bool("quiet", false, "hide per-round logs")
	flag.Parse()

	result, err := solveRemote(*hostFlag, *portFlag, *widthFlag, !*quietFlag)
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
