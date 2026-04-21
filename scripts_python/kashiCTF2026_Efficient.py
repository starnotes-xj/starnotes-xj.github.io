"""
kashiCTF 2026 - Efficient (Crypto)

题目描述：生成素数成本很高。我优化了密钥生成方法，速度提高了一倍。模数为 4096 位——绝对安全。

漏洞：n = p^2（p = q），直接开平方分解
解题流程：isqrt(n) → phi = p*(p-1) → RSA 解密得 AES 密钥 → AES-CBC 解密得 flag
"""

from math import isqrt
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

# ============================================================
# 从 output.txt 提取的参数
# ============================================================
n = 0x752a94a112ba0ce096f47934dac094d3d07b8c036613938142c0d4c15fc82692eee38d2457dd8d16472c4ddbe8cb5e2a6331e0ca0351094fc9516559768ebfe44509154d64116fa1fe1daf698413d37c9fe3406555f3190e29d99bee0cdd663d531c8e818f2686c7ad24338b4e93c6bfbd1b5a6dc5161316b2cb9ac1ae05a4ac43fdeb3b024b2e00dfcd87069ea1645996d9ad16ac3a9697414c17279112303a1d21136a99dc47628e15a3d6e18779de7aec310331dff1a81871b03e214de09f56c0f3de02f9f399be4ebc094f34b578d311a8b48e9c6cf2fa2f4e321f1dab0a99e5b9d99464c19452d9cc21544ac8e32fb9f13d1b2990758de0876de465cbd3632f846ef49fd7b97abee2ce529cfbc75a0d0792df6cc8091198134e9f646cf7d33c85c4ddd2c4b9a248c2c470d7369ebc7245bcec049455da2ceb742b26058514418398149d03cd1ad74a997375d0462a43e73aa62fc1f7e0dcc67e8f1559073074b9b8d3c37edfcfce67fd1822227933c5a14425d76119fc0a25da4c059761c86bc3077c4d096d9b9f6ae2faf728dbf24d48fa74d99c8c0d8780d2963ca9eccef0dd847ce22fc5b13793981257a9d4dd1af965e9baa5bd9fc4e3321cf8c6fd9871e342e5ae0dff19ab6e9fd8e14b5cc766b92df3306ef63af248b019528928644007c17e31918f9fdf10daeadc1eb8abeb6297bdc8f8e9b27c591f12159479
e = 65537

# RSA 密文（Base64）— 解密后得到 AES 密钥
ct_b64 = "MVoAMG4KRlXdSxEtVL/GpwXWyelWmAsJJhMnPaTzF2Hhjm/h/vkHJKQIyHSld2XuB6Q0sWq/TN1dkSePEB1oq6ugzMcgp5VQ9Xn0mOCn1GZ7fP3bKUVD6mG1bt3dkHxzlAT7v6c6xKaTtJJKTV3JXnB2u3duW4dCrFyassEjHM1PEML3CWqJBrgxnlTIYI4i9ydwg1MF1fTOBTm2KLlQ6rIGnBWcGwg4k+8I7e0mIbhod53w3FzIPXePv0ONVp+HBn4XsICwEHhJLXixmHcEz0jxwCgRdz9qr+Ur1pOaVuKN/26cwpYdVTlY5Fk7KapoV3Ews69353gCa+QYiJtzuwr1uFTBe74GfZZ8xzxFK51TnMbqB1M5cpzBK8/TK+ES/+yy1R4jsGkQ4i7Qz0oAsqBoNExSaLsNgwzZe4dYRE2BwDy2tW2QAYFUeU+SVjUb2BI67QtQYl2g+GB0kAMzbcRFr/kykIHqqb2N05BxgRrtsFjq2zWvpJJ71OFCrWVg8IzO7N+WUXFFyFv7ZfdnKOhC/iPNNmLbJXa3Gul89Fa6VyvCJw6lA/t7QCsjtcVG7ox51JAvoHhw5FLIpT+wmfq969iUujkXzLpjyXBVrfnEdjRt61zGEd3tmWIYst721GcKnbxKBehxwpseDBYR0hJRy+CIf5SnrP6/Blq55cQ="

# AES-CBC 参数 — 用于解密 flag
iv_b64 = "XSCnpZLyN1Oin7F67hOKWQ=="
flag_ct_b64 = "n+H1n3ezKEm0ulyLMcp/ShxLZAddKX7y848o/Lf/56qDev/DPBz+IRcJ14yHWGOuodMaMwyLZi9er7slNa+QMw=="

# ============================================================
# Step 1: 分解 n = p^2
# 题目 "速度提高一倍" 暗示只用了一个素数，n = p * p
# ============================================================
print("[*] Step 1: 分解 n = p^2")
p = isqrt(n)
if p * p != n:
    p += 1
assert p * p == n, "n 不是完全平方数，需要其他分解方法"
print(f"[+] 分解成功: n = p^2")
print(f"[+] p ({p.bit_length()} bits) = {hex(p)[:40]}...")

# ============================================================
# Step 2: 计算 RSA 私钥
# 对于 n = p^2，欧拉函数 φ(p^2) = p * (p - 1)
# ============================================================
print("\n[*] Step 2: 计算 RSA 私钥 d")
phi = p * (p - 1)
d = pow(e, -1, phi)
print(f"[+] d = {hex(d)[:40]}...")

# ============================================================
# Step 3: RSA 解密 ct，提取 AES 密钥
# ============================================================
print("\n[*] Step 3: RSA 解密提取 AES 密钥")
ct_bytes = base64.b64decode(ct_b64)
ct_int = int.from_bytes(ct_bytes, 'big')
pt_int = pow(ct_int, d, n)
pt_bytes = pt_int.to_bytes(512, 'big')  # 4096 bits = 512 bytes

# 去除前导零，取最后 16 字节作为 AES-128 密钥
aes_key = pt_bytes.lstrip(b'\x00')
print(f"[+] 解密后明文长度: {len(aes_key)} bytes")
print(f"[+] AES 密钥: {aes_key.hex()}")

# ============================================================
# Step 4: AES-CBC 解密获取 flag
# ============================================================
print("\n[*] Step 4: AES-CBC 解密获取 flag")
iv = base64.b64decode(iv_b64)
flag_ct = base64.b64decode(flag_ct_b64)

cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
flag = unpad(cipher_aes.decrypt(flag_ct), 16)
print(f"[+] Flag: {flag.decode()}")
