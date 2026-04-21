#!/usr/bin/env python3

import os
import sys
from Crypto.Cipher import AES

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass

# 从环境变量动态获取FLAG
FLAG = os.environ.get("FLAG", "novruzCTF{test}").encode()

KEY = os.urandom(16)
IV = bytes(16) 

def zero_pad(data: bytes) -> bytes:
    if len(data) % 16 != 0:
        return data + b'\x00' * (16 - len(data) % 16)
    return data

def cbc_mac(data: bytes) -> bytes:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    ct = cipher.encrypt(zero_pad(data))
    return ct[-16:]

def generate():
    known_msg = b"hello_world"
    known_mac = cbc_mac(known_msg)
    target_secret = b"get_flag"
    oracle_mac = cbc_mac(target_secret)

    print("=== Echoes of the Serpent ===")
    print("The Oracle speaks only to those who can weave new prophecies.")
    print("If you bring me a foreign whisper, the gates will open.")
    print("\nThe Oracle left behind a forgotten greeting:")
    print(f"Token('{known_msg.decode()}') = {known_mac.hex()}")
    print("\nIt also whispered the true name of the relic, but you cannot just repeat it:")
    print(f"Token('{target_secret.decode()}') = {oracle_mac.hex()}")
    
    try:
        print("\nSpeak your prophecy to the serpent!")
        msg_hex = input("Prophecy (Hex Msg)> ").strip()
        mac_hex = input("Seal (Hex Token)> ").strip()
        
        user_msg = bytes.fromhex(msg_hex)
        user_mac = bytes.fromhex(mac_hex)
        
        if user_msg == known_msg or user_msg == target_secret or user_msg == zero_pad(known_msg) or user_msg == zero_pad(target_secret):
            print("[-] The serpent hisses: 'I already know these words. Bring me something new.'")
            sys.exit(0)
            
        if len(user_msg) <= 16:
            print("[-] The serpent hisses: 'Your prophecy is too short. It lacks the echoes of the past.'")
            sys.exit(0)
            
        if cbc_mac(user_msg) == user_mac:
            print(f"[+] The gates open! The serpent rewards you: {FLAG.decode()}")
        else:
            print("[-] The seal is broken. The serpent ignores you.")
            
    except Exception as e:
        print("[-] The serpent cannot understand your strange tongue. (Hex only!)")

if __name__ == "__main__":
    generate()
