package main

import (
	"fmt"
	"math/big"
	"os"
	"regexp"
)

// mustParseNamedInt extracts a decimal integer after `key =` from challenge text.
func mustParseNamedInt(content, key string) *big.Int {
	pattern := `(?m)^` + regexp.QuoteMeta(key) + `\s*=\s*(\d+)\s*$`
	matches := regexp.MustCompile(pattern).FindStringSubmatch(content)
	if len(matches) != 2 {
		panic(fmt.Sprintf("cannot parse %s from input", key))
	}

	value, ok := new(big.Int).SetString(matches[1], 10)
	if !ok {
		panic(fmt.Sprintf("invalid integer for %s", key))
	}
	return value
}

// mustParseE extracts e as int.
func mustParseE(content string) int {
	exponent := mustParseNamedInt(content, "e")
	if !exponent.IsInt64() {
		panic("invalid integer for e")
	}
	return int(exponent.Int64())
}

// intKthRootFloor computes floor(n^(1/k)) using Newton iteration for big integers.
// This is much faster than binary-searching the root for every k candidate.
func intKthRootFloor(n *big.Int, k int64) *big.Int {
	if n.Sign() <= 0 {
		return new(big.Int)
	}
	if k <= 1 {
		return new(big.Int).Set(n)
	}

	one := big.NewInt(1)
	kBig := big.NewInt(k)
	kMinusOne := big.NewInt(k - 1)

	// Initial guess: 2^ceil(bitlen/k), normally above the true root.
	exp := (n.BitLen() + int(k) - 1) / int(k)
	x := new(big.Int).Lsh(one, uint(exp))

	for {
		// x_{t+1} = ((k-1)*x_t + n/x_t^(k-1)) / k
		xPow := new(big.Int).Exp(x, kMinusOne, nil)
		if xPow.Sign() == 0 {
			return new(big.Int).Set(x)
		}

		term1 := new(big.Int).Quo(n, xPow)
		term2 := new(big.Int).Mul(kMinusOne, x)
		next := new(big.Int).Add(term1, term2)
		next.Quo(next, kBig)

		// Newton converges from above here; when it no longer decreases, we refine locally.
		if next.Cmp(x) >= 0 {
			break
		}
		x = next
	}

	// Local correction to guarantee floor root.
	for new(big.Int).Exp(x, kBig, nil).Cmp(n) > 0 {
		x.Sub(x, one)
	}
	for {
		y := new(big.Int).Add(x, one)
		if new(big.Int).Exp(y, kBig, nil).Cmp(n) > 0 {
			break
		}
		x = y
	}
	return x
}

func main() {
	// Default input path follows this repository's attachment layout.
	inputPath := "CTF_Writeups/files/Exercise/exercise.txt"
	if len(os.Args) > 1 {
		inputPath = os.Args[1]
	}

	raw, err := os.ReadFile(inputPath)
	if err != nil {
		panic(fmt.Sprintf("read input failed: %v", err))
	}
	content := string(raw)

	n := mustParseNamedInt(content, "n")
	c := mustParseNamedInt(content, "c")
	e := mustParseE(content)
	if e <= 1 {
		panic("invalid exponent e")
	}

	// Core idea:
	//   m^e = c + k*n
	// The hint says m^e is only slightly larger than n,
	// so k is expected to be relatively small and can be searched.
	maxK := int64(2_000_000)
	e64 := int64(e)
	eBig := big.NewInt(e64)

	for k := int64(0); k <= maxK; k++ {
		candidate := new(big.Int).Mul(big.NewInt(k), n)
		candidate.Add(candidate, c)

		root := intKthRootFloor(candidate, e64)
		check := new(big.Int).Exp(root, eBig, nil)
		if check.Cmp(candidate) == 0 {
			// Exact e-th power found; decode big-endian bytes to plaintext.
			plaintext := root.Bytes()
			fmt.Printf("found k = %d\n", k)
			fmt.Printf("m (decimal) = %s\n", root.String())
			fmt.Printf("plaintext = %s\n", string(plaintext))
			return
		}
	}

	fmt.Printf("no exact root found in k range [0, %d]\n", maxK)
}
