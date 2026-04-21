package main

import (
	"crypto/md5"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"math"
	"math/rand"
	"os"
	"sync"
	"sync/atomic"
	"time"
)

const (
	width      = 150
	height     = 150
	channels   = 3
	totalBytes = width * height * channels
	totalPix   = width * height
)

func loadPixels(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return data, nil
}

func savePNG(pixels []byte, path string, scale float64) error {
	img := image.NewRGBA(image.Rect(0, 0, width, height))
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			idx := (y*width + x) * channels
			r := uint8(math.Min(float64(pixels[idx])*scale, 255))
			g := uint8(math.Min(float64(pixels[idx+1])*scale, 255))
			b := uint8(math.Min(float64(pixels[idx+2])*scale, 255))
			img.Set(x, y, color.RGBA{r, g, b, 255})
		}
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return png.Encode(f, img)
}

func savePNGDirect(pixels []byte, path string) error {
	img := image.NewRGBA(image.Rect(0, 0, width, height))
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			idx := (y*width + x) * channels
			img.Set(x, y, color.RGBA{pixels[idx], pixels[idx+1], pixels[idx+2], 255})
		}
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	return png.Encode(f, img)
}

// Method 1: XOR with Go rand - fast sample-based check
func methodGoRandXOR(data []byte, workers int) int64 {
	fmt.Println("\n=== Go rand XOR (sample filter) ===")
	start := time.Now()
	var found atomic.Int64
	found.Store(-1)
	var wg sync.WaitGroup
	chunkSize := 999001 / workers

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(wid int) {
			defer wg.Done()
			seedStart := int64(1000 + wid*chunkSize)
			seedEnd := seedStart + int64(chunkSize)
			if wid == workers-1 {
				seedEnd = 1000001
			}
			for seed := seedStart; seed < seedEnd; seed++ {
				if found.Load() >= 0 {
					return
				}
				rng := rand.New(rand.NewSource(seed))
				// Sample check: first 30 bytes
				uniqueMap := [256]bool{}
				uniqueCount := 0
				fail := false
				for i := 0; i < 30; i++ {
					val := data[i] ^ byte(rng.Intn(256))
					if !uniqueMap[val] {
						uniqueMap[val] = true
						uniqueCount++
						if uniqueCount > 10 {
							fail = true
							break
						}
					}
				}
				if fail {
					continue
				}
				// Full check
				rng2 := rand.New(rand.NewSource(seed))
				var fullUnique [256]bool
				fullUniqueCount := 0
				for i := 0; i < totalBytes; i++ {
					val := data[i] ^ byte(rng2.Intn(256))
					if !fullUnique[val] {
						fullUnique[val] = true
						fullUniqueCount++
					}
				}
				if fullUniqueCount < 50 {
					found.Store(seed)
					fmt.Printf("  FOUND! Seed=%d, unique=%d\n", seed, fullUniqueCount)
					return
				}
				if seed%500000 == 0 && wid == 0 {
					fmt.Printf("  Progress: ~%d (%.1fs)\n", seed, time.Since(start).Seconds())
				}
			}
		}(w)
	}
	wg.Wait()
	fmt.Printf("  Done in %.1fs\n", time.Since(start).Seconds())
	return found.Load()
}

// Method 2: SubMod - (pixel - noise) % 51
func methodGoRandSubMod(data []byte, workers int) int64 {
	fmt.Println("\n=== Go rand SubMod 51 ===")
	start := time.Now()
	var found atomic.Int64
	found.Store(-1)
	var wg sync.WaitGroup
	chunkSize := 999001 / workers

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(wid int) {
			defer wg.Done()
			seedStart := int64(1000 + wid*chunkSize)
			seedEnd := seedStart + int64(chunkSize)
			if wid == workers-1 {
				seedEnd = 1000001
			}
			for seed := seedStart; seed < seedEnd; seed++ {
				if found.Load() >= 0 {
					return
				}
				rng := rand.New(rand.NewSource(seed))
				var uniqueMap [52]bool
				uniqueCount := 0
				fail := false
				for i := 0; i < 30; i++ {
					val := byte((int(data[i]) - rng.Intn(51) + 51) % 51)
					if !uniqueMap[val] {
						uniqueMap[val] = true
						uniqueCount++
						if uniqueCount > 8 {
							fail = true
							break
						}
					}
				}
				if fail {
					continue
				}
				// Full check
				rng2 := rand.New(rand.NewSource(seed))
				var fullUnique [52]bool
				fullUniqueCount := 0
				for i := 0; i < totalBytes; i++ {
					val := byte((int(data[i]) - rng2.Intn(51) + 51) % 51)
					if !fullUnique[val] {
						fullUnique[val] = true
						fullUniqueCount++
					}
				}
				if fullUniqueCount < 10 {
					found.Store(seed)
					fmt.Printf("  FOUND! Seed=%d, unique=%d\n", seed, fullUniqueCount)
					return
				}
				if seed%500000 == 0 && wid == 0 {
					fmt.Printf("  Progress: ~%d (%.1fs)\n", seed, time.Since(start).Seconds())
				}
			}
		}(w)
	}
	wg.Wait()
	fmt.Printf("  Done in %.1fs\n", time.Since(start).Seconds())
	return found.Load()
}

// Method 3: Hash-based noise (MD5/SHA256 of seed+index)
func methodHashNoise(data []byte, workers int) int64 {
	fmt.Println("\n=== Hash-based noise (SHA256(seed||index) % 51) ===")
	start := time.Now()
	var found atomic.Int64
	found.Store(-1)
	var wg sync.WaitGroup
	chunkSize := 999001 / workers

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(wid int) {
			defer wg.Done()
			seedStart := 1000 + wid*chunkSize
			seedEnd := seedStart + chunkSize
			if wid == workers-1 {
				seedEnd = 1000001
			}
			buf := make([]byte, 8)
			for seed := seedStart; seed < seedEnd; seed++ {
				if found.Load() >= 0 {
					return
				}
				// Quick sample: check first 30 bytes
				binary.LittleEndian.PutUint32(buf[:4], uint32(seed))
				uniqueCount := 0
				var uniqueMap [52]bool
				fail := false
				for i := 0; i < 30; i++ {
					binary.LittleEndian.PutUint32(buf[4:], uint32(i))
					h := sha256.Sum256(buf)
					noise := h[0] % 51
					val := (data[i] - noise + 51) % 51
					if !uniqueMap[val] {
						uniqueMap[val] = true
						uniqueCount++
						if uniqueCount > 8 {
							fail = true
							break
						}
					}
				}
				if fail {
					continue
				}
				// Full check
				var fullUnique [52]bool
				fullUniqueCount := 0
				for i := 0; i < totalBytes; i++ {
					binary.LittleEndian.PutUint32(buf[4:], uint32(i))
					h := sha256.Sum256(buf)
					noise := h[0] % 51
					val := (data[i] - noise + 51) % 51
					if !fullUnique[val] {
						fullUnique[val] = true
						fullUniqueCount++
					}
				}
				if fullUniqueCount < 10 {
					found.Store(int64(seed))
					fmt.Printf("  FOUND! Seed=%d, unique=%d\n", seed, fullUniqueCount)
					return
				}
				if seed%100000 == 0 && wid == 0 {
					fmt.Printf("  Progress: ~%d (%.1fs)\n", seed, time.Since(start).Seconds())
				}
			}
		}(w)
	}
	wg.Wait()
	fmt.Printf("  Done in %.1fs\n", time.Since(start).Seconds())
	return found.Load()
}

// Method 4: MD5 hash noise
func methodMD5Noise(data []byte, workers int) int64 {
	fmt.Println("\n=== Hash-based noise (MD5(seed||index) % 51) ===")
	start := time.Now()
	var found atomic.Int64
	found.Store(-1)
	var wg sync.WaitGroup
	chunkSize := 999001 / workers

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(wid int) {
			defer wg.Done()
			seedStart := 1000 + wid*chunkSize
			seedEnd := seedStart + chunkSize
			if wid == workers-1 {
				seedEnd = 1000001
			}
			buf := make([]byte, 8)
			for seed := seedStart; seed < seedEnd; seed++ {
				if found.Load() >= 0 {
					return
				}
				binary.LittleEndian.PutUint32(buf[:4], uint32(seed))
				uniqueCount := 0
				var uniqueMap [52]bool
				fail := false
				for i := 0; i < 30; i++ {
					binary.LittleEndian.PutUint32(buf[4:], uint32(i))
					h := md5.Sum(buf)
					noise := h[0] % 51
					val := (data[i] - noise + 51) % 51
					if !uniqueMap[val] {
						uniqueMap[val] = true
						uniqueCount++
						if uniqueCount > 8 {
							fail = true
							break
						}
					}
				}
				if fail {
					continue
				}
				// Full check
				var fullUnique [52]bool
				fullUniqueCount := 0
				for i := 0; i < totalBytes; i++ {
					binary.LittleEndian.PutUint32(buf[4:], uint32(i))
					h := md5.Sum(buf)
					noise := h[0] % 51
					val := (data[i] - noise + 51) % 51
					if !fullUnique[val] {
						fullUnique[val] = true
						fullUniqueCount++
					}
				}
				if fullUniqueCount < 10 {
					found.Store(int64(seed))
					fmt.Printf("  FOUND! Seed=%d, unique=%d\n", seed, fullUniqueCount)
					return
				}
				if seed%100000 == 0 && wid == 0 {
					fmt.Printf("  Progress: ~%d (%.1fs)\n", seed, time.Since(start).Seconds())
				}
			}
		}(w)
	}
	wg.Wait()
	fmt.Printf("  Done in %.1fs\n", time.Since(start).Seconds())
	return found.Load()
}

// Method 5: Go rand pixel shuffle (optimized - gradient of first few rows only)
func methodGoRandShuffle(data []byte, workers int) int64 {
	fmt.Println("\n=== Go rand Pixel Shuffle (optimized) ===")
	start := time.Now()
	var found atomic.Int64
	found.Store(-1)
	var mu sync.Mutex
	var wg sync.WaitGroup
	chunkSize := 999001 / workers

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(wid int) {
			defer wg.Done()
			seedStart := int64(1000 + wid*chunkSize)
			seedEnd := seedStart + int64(chunkSize)
			if wid == workers-1 {
				seedEnd = 1000001
			}
			perm := make([]int, totalPix)
			result := make([]byte, totalBytes)

			for seed := seedStart; seed < seedEnd; seed++ {
				if found.Load() >= 0 {
					return
				}
				rng := rand.New(rand.NewSource(seed))
				for i := range perm {
					perm[i] = i
				}
				for i := totalPix - 1; i > 0; i-- {
					j := rng.Intn(i + 1)
					perm[i], perm[j] = perm[j], perm[i]
				}

				// Unshuffle
				for i := 0; i < totalPix; i++ {
					si := i * channels
					di := perm[i] * channels
					result[di] = data[si]
					result[di+1] = data[si+1]
					result[di+2] = data[si+2]
				}

				// Quick gradient check: first 5 rows only
				var sum float64
				count := 0
				checkRows := 10
				for y := 0; y < checkRows; y++ {
					for x := 0; x < width-1; x++ {
						i1 := (y*width + x) * channels
						i2 := (y*width + x + 1) * channels
						for c := 0; c < channels; c++ {
							d := int(result[i1+c]) - int(result[i2+c])
							if d < 0 {
								d = -d
							}
							sum += float64(d)
							count++
						}
					}
				}
				grad := sum / float64(count)

				if grad < 8.0 { // Much lower than noise (~17)
					mu.Lock()
					fmt.Printf("  LOW GRADIENT! Seed=%d, grad=%.2f\n", seed, grad)
					savePNG(result, fmt.Sprintf("needle_shuffle_%d.png", seed), 5)
					found.Store(seed)
					mu.Unlock()
					return
				}

				if seed%100000 == 0 && wid == 0 {
					fmt.Printf("  Progress: ~%d (%.1fs)\n", seed, time.Since(start).Seconds())
				}
			}
		}(w)
	}
	wg.Wait()
	fmt.Printf("  Done in %.1fs\n", time.Since(start).Seconds())
	return found.Load()
}

func main() {
	data, err := loadPixels("needle_pixels.bin")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	fmt.Printf("Loaded %d bytes, first 10: %v\n", len(data), data[:10])

	workers := 16

	// Try fast methods first
	if seed := methodGoRandXOR(data, workers); seed >= 0 {
		fmt.Printf("\n*** Solution: seed = %d ***\n", seed)
		rng := rand.New(rand.NewSource(seed))
		result := make([]byte, totalBytes)
		for i := range result {
			result[i] = data[i] ^ byte(rng.Intn(256))
		}
		savePNGDirect(result, "needle_solution.png")
		return
	}

	if seed := methodGoRandSubMod(data, workers); seed >= 0 {
		fmt.Printf("\n*** Solution: seed = %d ***\n", seed)
		rng := rand.New(rand.NewSource(seed))
		result := make([]byte, totalBytes)
		for i := range result {
			result[i] = byte((int(data[i]) - rng.Intn(51) + 51) % 51)
		}
		savePNG(result, "needle_solution.png", 5)
		return
	}

	if seed := methodGoRandShuffle(data, workers); seed >= 0 {
		fmt.Printf("\n*** Solution: seed = %d ***\n", seed)
		return
	}

	if seed := methodHashNoise(data, workers); seed >= 0 {
		fmt.Printf("\n*** Solution (SHA256): seed = %d ***\n", seed)
		return
	}

	if seed := methodMD5Noise(data, workers); seed >= 0 {
		fmt.Printf("\n*** Solution (MD5): seed = %d ***\n", seed)
		return
	}

	fmt.Println("\nNo solution found with tested methods.")
}
