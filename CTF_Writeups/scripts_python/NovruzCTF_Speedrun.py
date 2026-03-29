import re
import socket
import sys
import time

RULE_RE = re.compile(rb"'(.)'\s*=>\s*(\w+)")

OP_FALLBACK = {
    ord('+'): b'ADD',
    ord('-'): b'SUB',
    ord('*'): b'MUL',
    ord('/') : b'DIV',
    ord('%'): b'MOD',
    ord('^'): b'XOR',
    ord('&'): b'AND',
    ord('|'): b'OR',
}


def python_div(a, b):
    if b == 0:
        return 0
    return a // b


def python_mod(a, b):
    if b == 0:
        return 0
    return a % b


def int_pow(a, b):
    if b < 0:
        return 0
    return pow(a, b)


def apply_op(sym, a, b, op_map):
    op = op_map.get(sym) or OP_FALLBACK.get(sym)
    if op is None:
        return 0
    if op == b'ADD':
        return a + b
    if op == b'SUB':
        return a - b
    if op == b'MUL':
        return a * b
    if op == b'DIV':
        return python_div(a, b)
    if op == b'MOD':
        return python_mod(a, b)
    if op == b'XOR':
        return a ^ b
    if op == b'AND':
        return a & b
    if op == b'OR':
        return a | b
    if op == b'LSHIFT':
        return 0 if b < 0 or b > 63 else (a << b)
    if op == b'RSHIFT':
        return 0 if b < 0 or b > 63 else (a >> b)
    if op == b'POW':
        return int_pow(a, b)
    return 0


def parse_expr(expr, i, op_map):
    n = len(expr)
    while i < n and expr[i] == 32:
        i += 1
    if i >= n:
        return 0, i

    if expr[i] == ord('('):
        i += 1
        left, i = parse_expr(expr, i, op_map)
        while i < n and expr[i] == 32:
            i += 1
        if i < n and expr[i] == ord(')'):
            return left, i + 1
        op = expr[i]
        i += 1
        right, i = parse_expr(expr, i, op_map)
        while i < n and expr[i] == 32:
            i += 1
        if i < n and expr[i] == ord(')'):
            i += 1
        return apply_op(op, left, right, op_map), i

    start = i
    if i < n and expr[i] in (ord('+'), ord('-')):
        i += 1
    while i < n and 48 <= expr[i] <= 57:
        i += 1
    if start == i:
        return 0, i
    return int(expr[start:i]), i


def evaluate(expr, op_map):
    v, _ = parse_expr(expr, 0, op_map)
    return v


def main():
    addr = ("142.93.12.237", 1337)
    if len(sys.argv) > 1:
        host, port = sys.argv[1].split(':')
        addr = (host, int(port))

    s = socket.create_connection(addr, timeout=10)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    op_map = {}
    solved = 0
    start = time.time()

    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        while True:
            nl = buf.find(b'\n')
            if nl < 0:
                break
            line = buf[:nl]
            buf = buf[nl + 1:]
            if not line:
                continue

            if b'RULES:' in line:
                op_map = {m.group(1)[0]: m.group(2).upper() for m in RULE_RE.finditer(line)}
                continue

            if b'Calculate: ' in line:
                expr = line.split(b'Calculate: ', 1)[1].strip()
                res = evaluate(expr, op_map)
                s.sendall(str(res).encode() + b'\n')
                solved += 1
                if solved % 64 == 0:
                    elapsed = time.time() - start
                    sys.stderr.write(f"[*] {solved}/256 at {elapsed:.2f}s\n")
                continue

            trimmed = line.strip()
            if trimmed and not trimmed.startswith(b'####') and b'PROTOCOL UPDATE' not in trimmed:
                print(trimmed.decode(errors='ignore'))

    elapsed = time.time() - start
    print(f"[*] Solved: {solved}/256 in {elapsed:.2f}s")


if __name__ == '__main__':
    main()
