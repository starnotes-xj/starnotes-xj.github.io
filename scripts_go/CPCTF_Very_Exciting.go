package main

import (
	"bufio"
	"bytes"
	"encoding/hex"
	"flag"
	"fmt"
	"net"
	"regexp"
	"time"
)

// 题目利用点：
// 1. 服务先打印 flag 在 (secret_key, exciting_iv) 下的流密码密文；
// 2. 随后又开放“自选 IV + 自选明文”的加密 oracle，且仍然复用同一个 secret_key；
// 3. 如果把 IV 设成同一个 exciting_iv，并发送等长全 0 明文，返回值就会等于 keystream；
// 4. 再把 keystream 与 flag 密文异或，即可恢复原始 flag。

var (
	ivPattern         = regexp.MustCompile(`exciting_iv[^:：]*[:：]\s*([0-9a-f]+)`)
	ciphertextPattern = regexp.MustCompile(`=>\s*([0-9a-f]+)`)
)

func readUntilAny(reader *bufio.Reader, conn net.Conn, markers [][]byte) ([]byte, error) {
	var buffer bytes.Buffer
	for {
		data := buffer.Bytes()
		for _, marker := range markers {
			if bytes.Contains(data, marker) {
				return append([]byte(nil), data...), nil
			}
		}

		if err := conn.SetReadDeadline(time.Now().Add(10 * time.Second)); err != nil {
			return nil, err
		}

		b, err := reader.ReadByte()
		if err != nil {
			return append([]byte(nil), buffer.Bytes()...), err
		}
		buffer.WriteByte(b)
	}
}

func extractIVAndCiphertext(text string) (string, []byte, error) {
	ivMatch := ivPattern.FindStringSubmatch(text)
	cipherMatch := ciphertextPattern.FindStringSubmatch(text)
	if len(ivMatch) != 2 || len(cipherMatch) != 2 {
		return "", nil, fmt.Errorf("无法解析 exciting_iv / exciting_flag")
	}

	ciphertext, err := hex.DecodeString(cipherMatch[1])
	if err != nil {
		return "", nil, fmt.Errorf("无法解析 flag 密文字节: %w", err)
	}
	return ivMatch[1], ciphertext, nil
}

func xorBytes(left, right []byte) ([]byte, error) {
	if len(left) != len(right) {
		return nil, fmt.Errorf("异或双方长度不一致")
	}
	out := make([]byte, len(left))
	for i := range left {
		out[i] = left[i] ^ right[i]
	}
	return out, nil
}

func zeroHex(byteLen int) string {
	result := make([]byte, byteLen*2)
	for i := range result {
		result[i] = '0'
	}
	return string(result)
}

func hexToBytes(hexText string) ([]byte, error) {
	result, err := hex.DecodeString(hexText)
	if err != nil {
		return nil, fmt.Errorf("无法解析十六进制: %w", err)
	}
	return result, nil
}

func recoverFlag(host string, port int) (string, error) {
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 10*time.Second)
	if err != nil {
		return "", err
	}
	defer conn.Close()

	reader := bufio.NewReader(conn)
	initialMarkers := [][]byte{
		[]byte("Enter your boring 'favorite' (Hex): "),
		[]byte("输入你无聊的“最爱”（十六进制）: "),
	}
	secondMarkers := [][]byte{
		[]byte("Enter your own 'very_exciting' IV (Hex): "),
		[]byte("Enter your own 'very_exciting' IV (Hex):"),
	}

	banner, err := readUntilAny(reader, conn, initialMarkers)
	if err != nil {
		return "", err
	}

	excitingIVHex, excitingFlag, err := extractIVAndCiphertext(string(banner))
	if err != nil {
		return "", err
	}

	if _, err = fmt.Fprintf(conn, "%s\n", zeroHex(len(excitingFlag))); err != nil {
		return "", err
	}

	if _, err = readUntilAny(reader, conn, secondMarkers); err != nil {
		return "", err
	}
	if _, err = fmt.Fprintf(conn, "%s\n", excitingIVHex); err != nil {
		return "", err
	}

	var response bytes.Buffer
	for {
		if err = conn.SetReadDeadline(time.Now().Add(5 * time.Second)); err != nil {
			return "", err
		}
		chunk := make([]byte, 4096)
		n, readErr := reader.Read(chunk)
		if n > 0 {
			response.Write(chunk[:n])
		}
		if readErr != nil {
			netErr, ok := readErr.(net.Error)
			if ok && netErr.Timeout() {
				break
			}
			break
		}
	}

	keystreamMatch := ciphertextPattern.FindStringSubmatch(response.String())
	if len(keystreamMatch) != 2 {
		return "", fmt.Errorf("无法解析 keystream")
	}
	keystream, err := hexToBytes(keystreamMatch[1])
	if err != nil {
		return "", err
	}

	flagBytes, err := xorBytes(excitingFlag, keystream)
	if err != nil {
		return "", err
	}
	return string(flagBytes), nil
}

func main() {
	host := flag.String("host", "133.88.122.244", "challenge host")
	port := flag.Int("port", 32007, "challenge port")
	flag.Parse()

	result, err := recoverFlag(*host, *port)
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
