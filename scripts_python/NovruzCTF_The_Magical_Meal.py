import math
import random

# ======================== 参数 ========================
# 从图片中读取的 ElGamal 参数
p_str = "1905671816403772611477075447515791022372594380344434356222414517909417652709503859707116441682578631751"
g_str = "35184372088891"
h_str = "51604037746295575257434694992797642501681250360811180981081060940424101015886204338530685374507425988​2"
c1_str = "13251053023241332020308632831721495676720694896334569119269980510533474438817146321474966159216834357​10"
c2_str = "11056527390041988343879110954122996897662668728642448446777690219172267373214290325892278730831161042​28"


def clean_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def is_probable_prime(n: int) -> bool:
    if n < 2:
        return False
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in small_primes:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def pollard_rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    while True:
        x = random.randrange(2, n - 1)
        y = x
        c = random.randrange(1, n - 1)
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


def factorize(n: int) -> dict:
    factors = {}
    if n <= 1:
        return factors

    limit = 1_000_000
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start: limit + 1: step] = b"\x00" * ((limit - start) // step + 1)
    small_primes = [i for i in range(2, limit + 1) if sieve[i]]

    for p in small_primes:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p

    def rec(m: int):
        if m <= 1:
            return
        if is_probable_prime(m):
            factors[m] = factors.get(m, 0) + 1
            return
        d = pollard_rho(m)
        rec(d)
        rec(m // d)

    if n > 1:
        rec(n)
    return factors


def bsgs(g: int, h: int, p: int, order: int) -> int | None:
    m = int(math.isqrt(order)) + 1
    table = {}
    e = 1
    for j in range(m):
        table[e] = j
        e = (e * g) % p
    gm = pow(g, m, p)
    gm_inv = modinv(gm, p)
    gamma = h
    for i in range(m):
        if gamma in table:
            return (i * m + table[gamma]) % order
        gamma = (gamma * gm_inv) % p
    return None


def crt(residues: list[int], moduli: list[int]) -> int:
    if not residues:
        return 0
    M = 1
    for m in moduli:
        M *= m
    result = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        yi = modinv(Mi, m)
        result = (result + r * Mi * yi) % M
    return result


def pohlig_hellman(g: int, h: int, p: int, group_order: int, factors: dict) -> int:
    residues = []
    moduli = []
    for q, e in factors.items():
        qe = q ** e
        exp = group_order // qe
        g_prime = pow(g, exp, p)
        h_prime = pow(h, exp, p)
        print(f"  子群 q={q}, e={e}, q^e={qe} ... ", end="")
        if e == 1:
            xi = bsgs(g_prime, h_prime, p, q)
            if xi is None:
                print("BSGS 失败!")
                continue
            print(f"x_{q} = {xi}")
            residues.append(xi)
            moduli.append(qe)
        else:
            g_base = pow(g, group_order // q, p)
            xi = 0
            for k in range(e):
                qk1 = q ** (k + 1)
                exp_k = group_order // qk1
                g_inv_xi = modinv(pow(g, xi, p), p)
                hk = pow((h * g_inv_xi) % p, exp_k, p)
                dk = bsgs(g_base, hk, p, q)
                if dk is None:
                    dk = 0
                xi += dk * (q ** k)
            print(f"x mod {qe} = {xi}")
            residues.append(xi)
            moduli.append(qe)
    return crt(residues, moduli)


def main():
    p = int(clean_digits(p_str))
    g = int(clean_digits(g_str))
    h = int(clean_digits(h_str))
    c1 = int(clean_digits(c1_str))
    c2 = int(clean_digits(c2_str))

    print(f"p  = {p}")
    print(f"g  = {g}")
    print(f"h  = {h}")
    print(f"c1 = {c1}")
    print(f"c2 = {c2}")
    print(f"p 位数: {len(str(p))}, 比特: {p.bit_length()}")
    print(f"p 是素数: {is_probable_prime(p)}\n")

    print("=== Step 1: 分解 p-1 ===")
    p_minus_1 = p - 1
    print(f"p-1 = {p_minus_1}")
    factors = factorize(p_minus_1)
    print("p-1 的素因子分解:")
    check = 1
    for q, e in sorted(factors.items()):
        check *= q ** e
        print(f"  {q} ^ {e}")
    print(f"分解验证: {check == p_minus_1}\n")

    max_factor = max(factors.keys()) if factors else 0
    print(f"最大素因子: {max_factor} ({max_factor.bit_length()} bits)\n")

    print("=== Step 2: Pohlig-Hellman 求离散对数 ===")
    x = pohlig_hellman(g, h, p, p_minus_1, factors)
    print(f"私钥 x = {x}\n")

    h_check = pow(g, x, p)
    print(f"验证 g^x mod p == h: {h_check == h}\n")

    if h_check != h:
        raise SystemExit("错误: 离散对数验证失败!")

    print("=== Step 3: ElGamal 解密 ===")
    s = pow(c1, x, p)
    s_inv = modinv(s, p)
    m = (c2 * s_inv) % p
    m_bytes = m.to_bytes((m.bit_length() + 7) // 8, "big")
    print(f"明文 m = {m}")
    print(f"十六进制: {m_bytes.hex()}")
    try:
        print(f"文本: {m_bytes.decode()}")
    except UnicodeDecodeError:
        print("文本: <decode error>")


if __name__ == "__main__":
    main()
