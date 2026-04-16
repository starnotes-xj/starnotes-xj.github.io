import json, os, shlex

from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Cipher import AES

KEY = get_random_bytes(16)
FLAG = os.environ.get("FLAG", "dach2026{test_flag}")

print("Welcome to SafeShell™")
print("Use 'help' to list available commands")

state = {"admin": False, "notes": "use 'notes <your notes here>' to update notes!"}

while True:
    try:
        args = shlex.split(input("> "))
        if not args:
            continue

        cmd = args[0]
        arg = " ".join(args[1:])

        if cmd == "help":
            print("help    - print available commands")
            print("exit    - exit SafeShell™")
            print("notes   - get or set shell notes")
            print("save    - save shell state")
            print("restore - restore saved shell state")
            if not state["admin"]:
                print("logon   - log on as a SafeShell™ administrator")
            else:
                print("logoff  - log off as a SafeShell™ administrator")
                print("flag    - print the SafeShell™ secret flag")

        elif cmd == "exit":
            exit()

        elif cmd == "notes":
            if not arg:
                print(f"Notes: {state["notes"]}")
            else:
                state["notes"] = arg
                print("Saved shell notes")

        elif cmd == "save":
            iv = get_random_bytes(16)
            pt = pad(json.dumps(state).encode(), 16)
            ct = iv + AES.new(KEY, AES.MODE_CBC, iv=iv).encrypt(pt)
            print(f"Saved shell state: {ct.hex()}")

        elif cmd == "restore":
            ct = bytes.fromhex(arg)
            pt = AES.new(KEY, AES.MODE_CBC, iv=ct[:16]).decrypt(ct[16:])
            state = json.loads(unpad(pt, 16).decode())
            print("Restored saved shell state")

        elif cmd == "logon" and not state["admin"]:
            if arg == get_random_bytes(32).hex():  # TODO: hook up to DB
                print("Welcome Administrator!")
                state["admin"] = True
            else:
                print("Password incorrect!")

        elif cmd == "logoff" and state["admin"]:
            print("Goodbye Administrator!")
            state["admin"] = False

        elif cmd == "flag" and state["admin"]:
            print(f"Flag: {FLAG}")

        else:
            print("Unknown command")
    except KeyboardInterrupt:
        break
    except Exception as err:
        print(f"Failed to execute command: {err}")
