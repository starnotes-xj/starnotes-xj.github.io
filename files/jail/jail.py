#!/usr/bin/env python3
import string
import subprocess

ALLOWED = set("cpctf" + string.punctuation)
LEN_LIMIT = 2 + 0 + 2 + 6
data = input("> ").strip()
if set(data) <= ALLOWED and len(data) <= LEN_LIMIT:
    try:
        subprocess.run(["/bin/bash", "-c", data], timeout=1)
    except subprocess.TimeoutExpired:
        print("timeout")
else:
    print("invalid input")
