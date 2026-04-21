from Crypto.Util.number import bytes_to_long, long_to_bytes

flag = "CPCTF{REDACTED}"
flag_bytes = flag.encode()
print(f"c = {bytes_to_long(flag_bytes)}")
print(long_to_bytes(510812092313572375684202062709941424740135938555245927502061365582594139087652994941))