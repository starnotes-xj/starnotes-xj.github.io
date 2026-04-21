#!/usr/local/bin/python3
from os import getenv, urandom


class BoringRandom:
    C0 = 0x6A09E667F3BCC908
    C1 = 0xBB67AE8584CAA73B
    C2 = 0x3C6EF372FE94F82B

    SBOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    ]

    def __init__(self, key: bytes, iv: bytes):
        assert len(key) == 16 and len(iv) == 16

        K0 = int.from_bytes(key[0:8], byteorder='big')
        K1 = int.from_bytes(key[8:16], byteorder='big')
        I0 = int.from_bytes(iv[0:8], byteorder='big')
        I1 = int.from_bytes(iv[8:16], byteorder='big')

        self.a = [0] * 3
        self.b = [0] * 16

        self.a[0] = K0
        self.a[1] = K1
        self.a[2] = self._rotl(K0, 7) ^ self._rotr(K1, 7) ^ self.C0

        for i in range(16):
            self._update_rho_only()
            self.b[15 - i] = self.a[0]

        self.a[0] ^= I0
        self.a[1] ^= I1
        self.a[2] ^= self._rotl(I0, 7) ^ self._rotr(I1, 7) ^ self.C0

        for i in range(16):
            self._update_rho_only()

        for i in range(16):
            self._update()

    def nextrand(self) -> bytes:
        out = self.a[2]
        self._update()
        return out.to_bytes(8)

    def _update(self):
        a_0_next = self.a[1]
        a_1_next = self.a[2] ^ self._F(self.a[1], self.b[4]) ^ self.C1
        a_2_next = self.a[0] ^ self._F(
            self.a[1], self._rotl(self.b[10], 17)) ^ self.C2

        b_next = [0] * 16
        for j in range(16):
            if j not in (0, 4, 10):
                b_next[j] = self.b[j - 1]
        b_next[0] = self.b[15] ^ self.a[0]
        b_next[4] = self.b[3] ^ self.b[7]
        b_next[10] = self.b[9] ^ self._rotl(self.b[13], 32)

        self.a = [a_0_next, a_1_next, a_2_next]
        self.b = b_next

    def _update_rho_only(self):
        a_0_next = self.a[1]
        a_1_next = self.a[2] ^ self._F(self.a[1], 0) ^ self.C1
        a_2_next = self.a[0] ^ self._F(self.a[1], 0) ^ self.C2
        self.a = [a_0_next, a_1_next, a_2_next]

    def _F(self, X: int, B: int) -> int:
        O = X ^ B

        O_bytes = [(O >> ((7 - i) * 8)) & 0xFF for i in range(8)]

        P = [self.SBOX[b] for b in O_bytes]

        Q = [0] * 8
        for j in (0, 4):
            Q[j+0] = self._mul2(P[j+0]) ^ self._mul3(P[j+1]) ^ P[j+2] ^ P[j+3]
            Q[j+1] = P[j+0] ^ self._mul2(P[j+1]) ^ self._mul3(P[j+2]) ^ P[j+3]
            Q[j+2] = P[j+0] ^ P[j+1] ^ self._mul2(P[j+2]) ^ self._mul3(P[j+3])
            Q[j+3] = self._mul3(P[j+0]) ^ P[j+1] ^ P[j+2] ^ self._mul2(P[j+3])

        Y_bytes = [Q[4], Q[5], Q[2], Q[3], Q[0], Q[1], Q[6], Q[7]]

        Y = 0
        for b in Y_bytes:
            Y = (Y << 8) | b
        return Y

    def _rotl(self, x: int, n: int) -> int:
        return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF

    def _rotr(self, x: int, n: int) -> int:
        return ((x >> n) | (x << (64 - n))) & 0xFFFFFFFFFFFFFFFF

    def _mul2(self, x: int) -> int:
        return (x << 1) ^ 0x11b if (x & 0x80) else (x << 1)

    def _mul3(self, x: int) -> int:
        return self._mul2(x) ^ x


# 根据明文长度自动生成密钥流的辅助函数
def stream_excite(pksg, data: bytes) -> bytes:
    keystream = b""

    while len(keystream) < len(data):
        keystream += pksg.nextrand()

    return bytes([a ^ b for a, b in zip(data, keystream)])


def main():
    secret_key = urandom(16)
    exciting_iv = urandom(16)
    secret_flag_plaintext = getenv("FLAG", "FLAG{DUMMY}").encode()

    myPKSG = BoringRandom(secret_key, exciting_iv)

    exciting_flag = stream_excite(myPKSG, secret_flag_plaintext)
    print(f"这是我使用的exciting_iv！: {exciting_iv.hex()}")
    print(
        f"看哪！我的杰作，酷炫的令人兴奋的_flag！!\n => {exciting_flag.hex()}\n")

    print("现在轮到你们了，家里的朋友们！让我们让您“最喜欢”的事情变得令人兴奋！")

    favorite_input = input("输入你无聊的“最爱”（十六进制）: ")
    your_favorite = bytes.fromhex(favorite_input)
    if your_favorite == exciting_flag:
        print("哇哇哇！那是我的令人兴奋的标志！带上你自己无聊的东西！")
        exit(0)

    very_exciting_input = input("Enter your own 'very_exciting' IV (Hex): ")
    very_exciting_iv = bytes.fromhex(very_exciting_input)
    if len(very_exciting_iv) != 16:
        print("That's not a very exciting IV...")
        exit(0)
    yourPKSG = BoringRandom(secret_key, very_exciting_iv)

    enc_your_favorite = stream_excite(yourPKSG, your_favorite)
    print(
        f"Your favorite just got completely EXCITED!!\n => {enc_your_favorite.hex()}")

    tea_list = ["Black tea", "Green tea",
                "Oolong tea", "White tea", "Matcha", "Tisane"]
    destiny_tea_index = int.from_bytes(yourPKSG.nextrand()) % 6
    print(
        f"是时候冷静下来了。今天令人兴奋的茶神签 说... [{tea_list[destiny_tea_index]}]! Enjoy!")


if __name__ == '__main__':
    try:
        main()
    except:
        print("\nOops, looks like we got too excited and short-circuited. Bye!")
