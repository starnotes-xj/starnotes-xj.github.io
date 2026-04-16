package main

import (
	"bytes"
	"encoding/hex"
	"flag"
	"fmt"
	"net"
	"os"
	"regexp"
	"time"
)

// ACSC Qualification 2026 - SafeShell
//
// 利用点：
//   1. 服务端使用 AES-CBC 加密 JSON state
//   2. restore 时没有 MAC / AEAD 完整性校验
//   3. 第一块明文可预测，可以直接修改 IV 完成 CBC bit flipping
//
// 目标：
//   把首块明文从 {"admin": false, 改成 {"admin": true,
//
// 运行示例：
// go run CTF_Writeups/scripts_go/ACSC2026Qualification_SafeShell.go \
//   -host port.dyn.acsc.land -port 31582

var (
	prompt        = []byte("> ")
	originalBlock = []byte(`{"admin": false,`)
	targetBlock   = []byte(`{"admin": true, `)
	savePattern   = regexp.MustCompile(`Saved shell state: ([0-9a-f]+)`)
)

func recvUntil(conn net.Conn, marker []byte) ([]byte, error) {
	buffer := make([]byte, 0, 4096)
	chunk := make([]byte, 4096)

	for !bytes.Contains(buffer, marker) {
		if err := conn.SetReadDeadline(time.Now().Add(10 * time.Second)); err != nil {
			return nil, err
		}

		n, err := conn.Read(chunk)
		if err != nil {
			if len(buffer) > 0 {
				return buffer, nil
			}
			return nil, err
		}
		buffer = append(buffer, chunk[:n]...)
	}
	return buffer, nil
}

func sendLine(conn net.Conn, line []byte) error {
	payload := append(append([]byte{}, line...), '\n')
	_, err := conn.Write(payload)
	return err
}

func xor3(left, middle, right []byte) []byte {
	out := make([]byte, len(left))
	for i := range left {
		out[i] = left[i] ^ middle[i] ^ right[i]
	}
	return out
}

func exploit(host string, port int) ([]byte, error) {
	if len(originalBlock) != 16 || len(targetBlock) != 16 {
		return nil, fmt.Errorf("known plaintext blocks must be exactly 16 bytes")
	}

	conn, err := net.DialTimeout("tcp", fmt.Sprintf("%s:%d", host, port), 10*time.Second)
	if err != nil {
		return nil, err
	}
	defer conn.Close()

	var transcript []byte

	banner, err := recvUntil(conn, prompt)
	if err != nil {
		return nil, fmt.Errorf("read banner failed: %w", err)
	}
	transcript = append(transcript, banner...)

	if err := sendLine(conn, []byte("save")); err != nil {
		return nil, fmt.Errorf("send save failed: %w", err)
	}
	saveOutput, err := recvUntil(conn, prompt)
	if err != nil {
		return nil, fmt.Errorf("read save output failed: %w", err)
	}
	transcript = append(transcript, saveOutput...)

	matches := savePattern.FindSubmatch(saveOutput)
	if len(matches) != 2 {
		return nil, fmt.Errorf("could not parse saved state ciphertext")
	}

	ciphertext, err := hex.DecodeString(string(matches[1]))
	if err != nil {
		return nil, fmt.Errorf("decode ciphertext failed: %w", err)
	}
	if len(ciphertext) < 32 {
		return nil, fmt.Errorf("ciphertext too short to contain IV and one block")
	}

	originalIV := ciphertext[:16]
	encryptedBody := ciphertext[16:]
	forgedIV := xor3(originalIV, originalBlock, targetBlock)
	forgedCiphertext := append(append([]byte{}, forgedIV...), encryptedBody...)
	forgedHex := []byte(hex.EncodeToString(forgedCiphertext))

	restoreCommand := append([]byte("restore "), forgedHex...)
	if err := sendLine(conn, restoreCommand); err != nil {
		return nil, fmt.Errorf("send restore failed: %w", err)
	}
	restoreOutput, err := recvUntil(conn, prompt)
	if err != nil {
		return nil, fmt.Errorf("read restore output failed: %w", err)
	}
	transcript = append(transcript, restoreOutput...)
	if !bytes.Contains(restoreOutput, []byte("Restored saved shell state")) {
		return nil, fmt.Errorf("restore did not succeed")
	}

	if err := sendLine(conn, []byte("flag")); err != nil {
		return nil, fmt.Errorf("send flag failed: %w", err)
	}
	flagOutput, err := recvUntil(conn, prompt)
	if err != nil {
		return nil, fmt.Errorf("read flag output failed: %w", err)
	}
	transcript = append(transcript, flagOutput...)

	return transcript, nil
}

func main() {
	host := flag.String("host", "port.dyn.acsc.land", "target host")
	port := flag.Int("port", 31582, "target port")
	flag.Parse()

	transcript, err := exploit(*host, *port)
	if err != nil {
		fmt.Fprintf(os.Stderr, "exploit failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Print(string(transcript))
}
