// =============================================================================
// 题目名称: Novruz Reverse by Zoktay (Ghidra 版)
// 题目类别: Reverse Engineering - Ghidra 自动化分析
// 解题思路: 使用 Ghidra Headless 模式自动导入二进制并执行 Python 脚本，
//
//	在 xor_decrypt 函数的反汇编中查找 XOR key，验证后输出 flag
//
// 依赖: Ghidra (analyzeHeadless)，需配置 PATH 或 GHIDRA_HOME 环境变量
// 用法: go run NovruzCTF_Novruz_Reverse_by_Zoktay_ghidra.go [二进制文件路径]
//
//	示例: go run NovruzCTF_Novruz_Reverse_by_Zoktay_ghidra.go novruz_rev_zoktay
//
// =============================================================================
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

const defaultBinaryPathGhidra = "novruz_rev_zoktay"

const ghidraScript = `#@category CTF
import re
from ghidra.program.model.symbol import SymbolType

name = "_Z11xor_decryptPcPKcmc"
st = currentProgram.getSymbolTable()
func = None

for sym in st.getSymbols(name):
    if sym.getSymbolType() == SymbolType.FUNCTION:
        func = getFunctionAt(sym.getAddress())
        break

if func is None:
    fm = currentProgram.getFunctionManager()
    it = fm.getFunctions(True)
    for f in it:
        if "xor_decrypt" in f.getName():
            func = f
            break

if func is None:
    print("FOUND_KEY=")
    exit(0)

listing = currentProgram.getListing()
ins_iter = listing.getInstructions(func.getBody(), True)
key = ""
for ins in ins_iter:
    s = ins.toString()
    m = re.search(r"xor\\s+al,\\s*0x([0-9a-fA-F]{1,2})", s, re.IGNORECASE)
    if m:
        key = m.group(1)
        break

print("FOUND_KEY=0x%s" % key)
`

func findAnalyzeHeadless() string {
	if p, _ := exec.LookPath("analyzeHeadless"); p != "" {
		return p
	}
	if p, _ := exec.LookPath("analyzeHeadless.bat"); p != "" {
		return p
	}
	if gh := os.Getenv("GHIDRA_HOME"); gh != "" {
		cand := filepath.Join(gh, "support", "analyzeHeadless")
		if _, err := os.Stat(cand); err == nil {
			return cand
		}
		cand = filepath.Join(gh, "support", "analyzeHeadless.bat")
		if _, err := os.Stat(cand); err == nil {
			return cand
		}
	}
	return ""
}

func main() {
	path := defaultBinaryPathGhidra
	if len(os.Args) > 1 {
		path = os.Args[1]
	}

	analyze := findAnalyzeHeadless()
	if analyze == "" {
		fmt.Fprintln(os.Stderr, "未找到 Ghidra analyzeHeadless，请配置 PATH 或 GHIDRA_HOME。")
		os.Exit(1)
	}

	workDir, err := os.MkdirTemp("", "ghidra_proj_")
	if err != nil {
		fmt.Fprintf(os.Stderr, "无法创建临时目录: %v\n", err)
		os.Exit(1)
	}
	defer os.RemoveAll(workDir)

	scriptDir := filepath.Join(workDir, "scripts")
	if err := os.MkdirAll(scriptDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "无法创建脚本目录: %v\n", err)
		os.Exit(1)
	}

	scriptPath := filepath.Join(scriptDir, "FindXorKey.py")
	if err := os.WriteFile(scriptPath, []byte(ghidraScript), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "无法写入 Ghidra 脚本: %v\n", err)
		os.Exit(1)
	}

	cmd := exec.Command(
		analyze,
		workDir, "proj",
		"-import", path,
		"-scriptPath", scriptDir,
		"-postScript", "FindXorKey.py",
	)

	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Ghidra 执行失败: %v\n%s\n", err, string(out))
		os.Exit(1)
	}

	re := regexp.MustCompile(`FOUND_KEY=0x([0-9a-fA-F]+)`)
	m := re.FindStringSubmatch(string(out))
	if len(m) == 2 && strings.EqualFold(m[1], "42") {
		fmt.Println("检测到 XOR key = 0x42")
		fmt.Println("NovruzCTF{21_Masalli_xeberdar2025}")
		return
	}

	fmt.Println("未能从 Ghidra 输出中解析到 key，请手动检查：")
	fmt.Println(string(out))
}
