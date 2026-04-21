#!/usr/bin/env python3
"""
encrypt.py — RSA encryption used to produce public.txt.

A secret flag is padded with a known prefix and suffix, then encrypted
under RSA with a small public exponent.
"""

import sys
from Crypto.Util.number import bytes_to_long

# RSA public key (same for all instances)
n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
e = 3

def encrypt(flag: bytes) -> int:
    """Pad the flag and encrypt under RSA."""
    prefix = b"SDGCTF_SECURE_MSG_V1::"
    suffix = b"::END"

    padded = prefix + flag + suffix
    m = bytes_to_long(padded)

    if m >= n:
        raise ValueError("Message too large for modulus")

    return pow(m, e, n)

if __name__ == "__main__":
    flag = open("flag.txt", "rb").read().strip()
    c = encrypt(flag)
    print(f"n = {n}")
    print(f"e = {e}")
    print(f"c = {c}")
    print(f"flag_length = {len(flag)}")
