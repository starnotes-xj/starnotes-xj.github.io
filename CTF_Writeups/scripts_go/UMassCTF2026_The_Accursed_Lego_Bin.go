package main

import (
	"fmt"
	"math/big"
	"os"
	"strings"
)

const (
	mtN = 624
	mtM = 397
)

var (
	mask32 = new(big.Int).SetUint64(0xffffffff)
	one    = big.NewInt(1)
)

type pyMT19937 struct {
	state [mtN]uint32
	index int
}

func newPyMT19937FromBig(seed *big.Int) *pyMT19937 {
	rng := &pyMT19937{}
	rng.seed(seed)
	return rng
}

func (r *pyMT19937) seed(seed *big.Int) {
	n := new(big.Int).Abs(seed)
	keyUsed := 1
	if bits := n.BitLen(); bits > 0 {
		keyUsed = (bits-1)/32 + 1
	}

	key := make([]uint32, keyUsed)
	tmp := new(big.Int).Set(n)
	for i := 0; i < keyUsed; i++ {
		key[i] = uint32(new(big.Int).And(tmp, mask32).Uint64())
		tmp.Rsh(tmp, 32)
	}

	r.initByArray(key)
}

func (r *pyMT19937) initGenrand(seed uint32) {
	r.state[0] = seed
	for i := 1; i < mtN; i++ {
		prev := r.state[i-1]
		r.state[i] = 1812433253*(prev^(prev>>30)) + uint32(i)
	}
	r.index = mtN
}

func (r *pyMT19937) initByArray(key []uint32) {
	r.initGenrand(19650218)

	i, j := 1, 0
	k := mtN
	if len(key) > k {
		k = len(key)
	}

	for ; k > 0; k-- {
		r.state[i] = (r.state[i] ^ ((r.state[i-1] ^ (r.state[i-1] >> 30)) * 1664525)) + key[j] + uint32(j)
		i++
		j++
		if i >= mtN {
			r.state[0] = r.state[mtN-1]
			i = 1
		}
		if j >= len(key) {
			j = 0
		}
	}

	for k = mtN - 1; k > 0; k-- {
		r.state[i] = (r.state[i] ^ ((r.state[i-1] ^ (r.state[i-1] >> 30)) * 1566083941)) - uint32(i)
		i++
		if i >= mtN {
			r.state[0] = r.state[mtN-1]
			i = 1
		}
	}

	r.state[0] = 0x80000000
}

func (r *pyMT19937) genUint32() uint32 {
	const upperMask uint32 = 0x80000000
	const lowerMask uint32 = 0x7fffffff
	const matrixA uint32 = 0x9908b0df

	if r.index >= mtN {
		for i := 0; i < mtN; i++ {
			y := (r.state[i] & upperMask) | (r.state[(i+1)%mtN] & lowerMask)
			r.state[i] = r.state[(i+mtM)%mtN] ^ (y >> 1)
			if y&1 != 0 {
				r.state[i] ^= matrixA
			}
		}
		r.index = 0
	}

	y := r.state[r.index]
	r.index++

	y ^= y >> 11
	y ^= (y << 7) & 0x9d2c5680
	y ^= (y << 15) & 0xefc60000
	y ^= y >> 18
	return y
}

func (r *pyMT19937) getRandBits(k int) uint32 {
	if k <= 0 || k > 32 {
		panic("getRandBits supports 1..32 bits only")
	}
	return r.genUint32() >> (32 - k)
}

func (r *pyMT19937) randBelow(n int) int {
	if n <= 0 {
		panic("randBelow requires n > 0")
	}
	k := bitLength(n)
	v := int(r.getRandBits(k))
	for v >= n {
		v = int(r.getRandBits(k))
	}
	return v
}

func bitLength(n int) int {
	bits := 0
	for n > 0 {
		bits++
		n >>= 1
	}
	return bits
}

func parseOutput(path string) (*big.Int, string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}

	var seedText, flagHex string
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(strings.TrimRight(line, "\r"))
		switch {
		case strings.HasPrefix(line, "seed = "):
			seedText = strings.TrimSpace(strings.TrimPrefix(line, "seed = "))
		case strings.HasPrefix(line, "flag = "):
			flagHex = strings.TrimSpace(strings.TrimPrefix(line, "flag = "))
		}
	}

	if seedText == "" || flagHex == "" {
		return nil, "", fmt.Errorf("invalid output.txt format")
	}

	seed, ok := new(big.Int).SetString(seedText, 10)
	if !ok {
		return nil, "", fmt.Errorf("invalid seed integer")
	}
	return seed, flagHex, nil
}

func integerNthRootFloor(n *big.Int, degree int) *big.Int {
	if n.Sign() <= 0 {
		return new(big.Int)
	}
	if degree <= 1 {
		return new(big.Int).Set(n)
	}

	lo := new(big.Int)
	hi := new(big.Int).Lsh(one, uint((n.BitLen()+degree-1)/degree))
	if hi.Sign() == 0 {
		hi.Set(one)
	}

	for {
		pow := new(big.Int).Exp(hi, big.NewInt(int64(degree)), nil)
		if pow.Cmp(n) > 0 {
			break
		}
		hi.Lsh(hi, 1)
	}

	for new(big.Int).Sub(hi, lo).Cmp(one) > 0 {
		mid := new(big.Int).Add(lo, hi)
		mid.Rsh(mid, 1)

		pow := new(big.Int).Exp(mid, big.NewInt(int64(degree)), nil)
		if pow.Cmp(n) <= 0 {
			lo = mid
		} else {
			hi = mid
		}
	}
	return lo
}

func hexToBits(flagHex string) ([]byte, error) {
	raw, err := decodeHexString(flagHex)
	if err != nil {
		return nil, err
	}

	bits := make([]byte, 0, len(raw)*8)
	for _, b := range raw {
		for shift := 7; shift >= 0; shift-- {
			if (b>>shift)&1 == 1 {
				bits = append(bits, '1')
			} else {
				bits = append(bits, '0')
			}
		}
	}
	return bits, nil
}

func decodeHexString(text string) ([]byte, error) {
	if len(text)%2 != 0 {
		return nil, fmt.Errorf("invalid hex length")
	}

	raw := make([]byte, len(text)/2)
	for i := 0; i < len(raw); i++ {
		hi, ok := fromHexNibble(text[2*i])
		if !ok {
			return nil, fmt.Errorf("invalid hex character")
		}
		lo, ok := fromHexNibble(text[2*i+1])
		if !ok {
			return nil, fmt.Errorf("invalid hex character")
		}
		raw[i] = hi<<4 | lo
	}
	return raw, nil
}

func fromHexNibble(ch byte) (byte, bool) {
	switch {
	case ch >= '0' && ch <= '9':
		return ch - '0', true
	case ch >= 'a' && ch <= 'f':
		return ch - 'a' + 10, true
	case ch >= 'A' && ch <= 'F':
		return ch - 'A' + 10, true
	default:
		return 0, false
	}
}

func inverseShuffle(bits []byte, roundSeed *big.Int) []byte {
	rng := newPyMT19937FromBig(roundSeed)
	perm := make([]int, len(bits))
	for i := range perm {
		perm[i] = i
	}

	for i := len(perm) - 1; i > 0; i-- {
		j := rng.randBelow(i + 1)
		perm[i], perm[j] = perm[j], perm[i]
	}

	original := make([]byte, len(bits))
	for newPos, oldPos := range perm {
		original[oldPos] = bits[newPos]
	}
	return original
}

func bitsToASCII(bits []byte) (string, error) {
	if len(bits)%8 != 0 {
		return "", fmt.Errorf("bit length must be a multiple of 8")
	}

	out := make([]byte, 0, len(bits)/8)
	for i := 0; i < len(bits); i += 8 {
		var value byte
		for j := 0; j < 8; j++ {
			value <<= 1
			switch bits[i+j] {
			case '1':
				value |= 1
			case '0':
			default:
				return "", fmt.Errorf("invalid bit value")
			}
		}
		out = append(out, value)
	}
	return string(out), nil
}

func solve(path string) (string, error) {
	encSeed, flagHex, err := parseOutput(path)
	if err != nil {
		return "", err
	}

	shuffleSeed := integerNthRootFloor(encSeed, 7)
	if new(big.Int).Exp(shuffleSeed, big.NewInt(7), nil).Cmp(encSeed) != 0 {
		return "", fmt.Errorf("7th root recovery failed")
	}

	bits, err := hexToBits(flagHex)
	if err != nil {
		return "", err
	}

	for i := 9; i >= 0; i-- {
		roundSeed := new(big.Int).Mul(new(big.Int).Set(shuffleSeed), big.NewInt(int64(i+1)))
		bits = inverseShuffle(bits, roundSeed)
	}

	return bitsToASCII(bits)
}

func main() {
	path := "CTF_Writeups/files/The Accursed Lego Bin/output.txt"
	if len(os.Args) > 1 {
		path = os.Args[1]
	}

	flag, err := solve(path)
	if err != nil {
		fmt.Println("solve error:", err)
		os.Exit(1)
	}

	fmt.Println(flag)
}
