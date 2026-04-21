#!/usr/bin/env python3
"""
HackForAChange 2026 March - UN SDG3 - Patient Zero (Crypto)
RSA e=3 Stereotyped Message Attack (Coppersmith's method)

已知明文结构: prefix || flag || suffix
    prefix = b"SDGCTF_SECURE_MSG_V1::"
    suffix = b"::END"
    flag 长度 = 37 字节

攻击思路:
    e=3, 已知 padding 结构 → Coppersmith 小根攻击
    构造多项式 f(x) = (A + B·x)^3 - c ≡ 0 (mod n)
    其中 A 为已知常数部分, B = 256^5, x = flag (未知)
    |x| < 2^296 < n^(1/3) ≈ 2^341, 满足 Coppersmith 定理条件

依赖: SageMath (推荐 Docker 运行)
    docker run --rm -i sagemath/sagemath sage < this_script.sage
    或将下方 solve_sage() 的内容保存为 .sage 文件运行
"""

# ============================================================
# 方法一: SageMath 版本 (推荐, 代码简洁, 数秒出结果)
# ============================================================
# 将以下内容保存为 solve.sage 然后用 sage 运行:
SAGE_SCRIPT = r"""
n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
e = 3
c = 90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158

prefix = b'SDGCTF_SECURE_MSG_V1::'
suffix = b'::END'
flag_len = 37

# 计算已知常数部分
P = int.from_bytes(prefix, 'big')
S = int.from_bytes(suffix, 'big')
B = 256^len(suffix)                          # flag 的位移系数 (256^5)
A = P * 256^(flag_len + len(suffix)) + S     # 已知部分: prefix 左移 + suffix

# 构造多项式: f(x) = (A + B*x)^3 - c ≡ 0 (mod n)
# x = flag 的整数值, 是唯一未知量
ZmodN = Zmod(n)
PR = PolynomialRing(ZmodN, 'x')
x = PR.gen()
f = (A + B*x)^3 - c

# 转为首一多项式 (small_roots 要求)
f_monic = f * f.leading_coefficient()^(-1)

# Coppersmith small_roots: 在 |x| < X = 2^296 范围内搜索根
# epsilon 越小精度越高但耗时越长, 0.02 对本题足够
roots = f_monic.small_roots(X=2^(flag_len*8), beta=1.0, epsilon=0.02)
print(f'找到 {len(roots)} 个根: {roots}')

for r in roots:
    ri = int(r)
    # 验证: 代入原始加密检查
    m = A + B * ri
    if pow(m, 3, n) == c:
        flag = ri.to_bytes(flag_len, 'big')
        print(f'Flag: {flag.decode()}')
    else:
        print(f'根 {ri} 验证失败')
"""


# ============================================================
# 方法二: 纯 Python 版本 (无需 SageMath, 通过 Docker 调用)
# ============================================================
def solve_via_docker():
    """通过 Docker 运行 SageMath 求解"""
    import subprocess
    import tempfile
    import os

    # 写入临时 .sage 文件
    sage_code = SAGE_SCRIPT.strip()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sage', delete=False) as f:
        f.write(sage_code)
        sage_path = f.name

    try:
        # 通过 stdin 管道传入 Docker
        result = subprocess.run(
            ['docker', 'run', '--rm', '-i', 'sagemath/sagemath:latest', 'bash', '-c',
             'cat > /tmp/solve.sage && sage /tmp/solve.sage'],
            input=sage_code,
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    finally:
        os.unlink(sage_path)


# ============================================================
# 方法三: 纯 Python 验证 (已知 flag 后的验证脚本)
# ============================================================
def verify_flag():
    """验证已知 flag 的正确性"""
    from Crypto.Util.number import bytes_to_long

    n = 108060031931266353758801330782473639320039225201311917178449705019176660696244872351271382486864507377607807538618062847665115562029186118435965272613853246476229261400861607263122402792644231190189479726984543802757846539830277258662001776505200445021146928156972061161319057790512542181820218329738735817807
    e = 3
    c = 90774649037794866754680280280216764024691444983358017422974073995178100413886762031029662717088000194392511444035891491840195308233852093768325714409859719231254914688312929679278810851560152917544549149940293794049458294647149604501225858516434416279640156540194075205584845195544175768134585225460788063158

    flag = b"SDG{3c00bad87b9ba46afa47052e187cec59}"
    prefix = b"SDGCTF_SECURE_MSG_V1::"
    suffix = b"::END"

    padded = prefix + flag + suffix
    m = bytes_to_long(padded)
    c_check = pow(m, e, n)

    print(f"Flag: {flag.decode()}")
    print(f"Flag 长度: {len(flag)} bytes")
    print(f"Padded 长度: {len(padded)} bytes ({len(padded)*8} bits)")
    print(f"n 长度: {n.bit_length()} bits")
    print(f"m^3 约 {m.bit_length()*3} bits > n, 发生了模约化")
    print(f"加密验证: {'PASS' if c_check == c else 'FAIL'}")


if __name__ == "__main__":
    import sys

    if "--verify" in sys.argv:
        verify_flag()
    elif "--docker" in sys.argv:
        solve_via_docker()
    else:
        print("=" * 60)
        print("Patient Zero - RSA e=3 Coppersmith Attack")
        print("=" * 60)
        print()
        print("本题需要 SageMath 的 small_roots() 函数求解。")
        print()
        print("用法:")
        print("  1. Docker 方式 (推荐):")
        print("     python this_script.py --docker")
        print()
        print("  2. 直接用 SageMath:")
        print("     将 SAGE_SCRIPT 内容保存为 solve.sage")
        print("     sage solve.sage")
        print()
        print("  3. 验证已知 flag:")
        print("     python this_script.py --verify")
        print()
        print("--- 运行验证 ---")
        verify_flag()
