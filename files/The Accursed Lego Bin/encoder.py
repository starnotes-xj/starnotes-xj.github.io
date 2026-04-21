import random
import time
import dotenv
from Cryptodome.Util.number import getPrime
from Cryptodome.PublicKey import RSA

try:
    dotenv.load_dotenv()
    flag = dotenv.get_key(".env", "FLAG")
except KeyError:
    flag = "UMASS{simple_test_flag}"

e = 7

def RSA_enc(plain_text):
    p, q = getPrime(2048), getPrime(2048)
    n = p * q
    plain_num = int.from_bytes(plain_text.encode(), "big")
    ciphertext = pow(plain_num, e, n)
    return n, ciphertext

def get_flag_bits(flag):
    flag_bits = []
    for char in flag:
        char_bits = bin(ord(char))[2:].zfill(8)
        flag_bits.extend(char_bits)
    return flag_bits

def bit_arr_to_str(bit_arr):
    byte_arr = []
    for i in range(0, len(bit_arr), 8):
        byte = bit_arr[i:i+8]
        char = int(''.join(byte), 2)
        byte_arr.append(char)
    bytes_arr = bytes(byte_arr)
    return bytes.hex(bytes_arr)


def main():
    text = "I_LOVE_RNG"
    n, seed = RSA_enc(text)
    flag_bits = get_flag_bits(flag)
    for i in range(10):
        random.seed(seed*(i+1))
        random.shuffle(flag_bits)
    # now output the shuffled flag as binary
    enc_flag_bytes = bit_arr_to_str(flag_bits)
    enc_seed = pow(seed, e, n)
    with open("output.txt", "w") as f:
        f.write(f"seed = {enc_seed}\n")
        f.write(f"flag = {enc_flag_bytes}\n")

if __name__ == "__main__":
    main()