from Crypto.Util.number import (
    bytes_to_long, getPrime
)


def rsa_encryption(flag):
    m = bytes_to_long(flag.encode())
    e = 3
    p, q = getPrime(512), getPrime(512)
    n = p * q
    c = pow(n, e, m)
    return (n, e, c)


flag = "CPCTF{REDACTED_FLAG}"

n1, e1, c1 = rsa_encryption(flag)
print(f"n1 = {n1}")
print(f"e1 = {e1}")
print(f"c1 = {c1}")
n2, e2, c2 = rsa_encryption(flag)
print(f"n2 = {n2}")
print(f"e2 = {e2}")
print(f"c2 = {c2}")
