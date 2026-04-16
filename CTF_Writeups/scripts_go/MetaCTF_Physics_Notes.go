package main

import (
	"fmt"
	"os"
	"strings"
)

func extractFlag(text string) (string, error) {
	rawLines := strings.Split(text, "\n")
	lines := make([]string, 0, len(rawLines))
	for _, line := range rawLines {
		line = strings.TrimRight(line, "\r")
		if line == "" {
			continue
		}
		lines = append(lines, line)
	}

	if len(lines) < 15 {
		return "", fmt.Errorf("expected at least 15 non-empty lines")
	}

	var b strings.Builder
	for i := 0; i < 14; i++ {
		r := []rune(lines[i])
		b.WriteRune(r[0])
		b.WriteRune(r[len(r)-1])
	}

	last := []rune(lines[14])
	b.WriteRune(last[0])
	return b.String(), nil
}

func main() {
	data, err := os.ReadFile("CTF_Writeups/files/Physics Notes/notes.txt")
	if err != nil {
		fmt.Println("read error:", err)
		os.Exit(1)
	}

	flag, err := extractFlag(string(data))
	if err != nil {
		fmt.Println("extract error:", err)
		os.Exit(1)
	}

	fmt.Println(flag)
}
