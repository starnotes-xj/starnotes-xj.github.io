import os
import socketserver
from dataclasses import dataclass
from Crypto.Util.number import getPrime, long_to_bytes, bytes_to_long

FLAG = os.getenv("FLAG", "fake_flag")
print(FLAG)

primesize = 2048

@dataclass
class Dino:
    name: str
    dna: str
    vault_key: int

    @staticmethod
    def to_dna(dinosaur_information: str):
        lookup = ["A", "T", "G", "C"]
        dna = []
        for c in dinosaur_information:
            c = ord(c)
            for _ in range(4):
                dna.append(lookup[c & 3])
                c >>= 2
        return "".join(dna)

    def get_encrypted_dna(self):
        transmission_key = getPrime(primesize)
        dinosaur_modulation_index = transmission_key * sel2f.vault_key
        evergreen_number = 2**16 + 1
        resampled_dna = pow(bytes_to_long(self.dna.encode()), evergreen_number, dinosaur_modulation_index)
        encrypted_dna = long_to_bytes(resampled_dna).hex()
        return encrypted_dna, dinosaur_modulation_index

class DinoVaultServer(socketserver.StreamRequestHandler):
    def write(self, string):
        self.wfile.write(f"{string}\n".encode())

    def read(self):
        return self.rfile.readline().rstrip().decode("utf-8")

    def read_int(self):
        line = self.read()
        try:
            ret = int(line)
            return ret
        except ValueError:
            return 0
        return 0

    def prepare_dinos(self):
        self.dinos = [
            Dino(name="Vexillum Rex",  dna=Dino.to_dna(f"Has a crown and {FLAG} written on its back"), vault_key=getPrime(primesize)),
            Dino(name="Pedosaurus",    dna=Dino.to_dna("Has giant feet"), vault_key=getPrime(primesize)),
            Dino(name="Despotiraptor", dna=Dino.to_dna("Slightly sus ethics"), vault_key=getPrime(primesize)),
            Dino(name="Planosaurus",   dna=Dino.to_dna("Is floored when nothing goes to plan"), vault_key=getPrime(primesize)),
        ]

    def create(self):
        self.write("What is your dinosaur called?")
        name = self.read()
        self.write(f"Please give me all the information about {name}")
        info = self.read()
        self.write("Thanks, we have now sequenced your dinosaur.")
        vault_key = getPrime(primesize)
        self.write(f"To access your dino, you will need this key: {vault_key}")
        self.dinos.append(Dino(name=name, dna=Dino.to_dna(info), vault_key=vault_key))

    def view(self):
        self.write("We have the following selection of dinosaurs available:")
        for dino in self.dinos:
            self.write(f"- {dino.name}")

    def download(self):
        self.write("Which encrypted dinosaur-DNA do you want to download?")
        name = self.read()
        for dino in self.dinos:
            if name == dino.name:
                break
        else:
            self.write("Could not find the dino you were looking for")
            return
        self.write("Here is the encrypted DNA you wanted:")
        enc_dna, mod_index = dino.get_encrypted_dna()
        self.write(enc_dna)
        self.write("Use your vault key alongside the modulation index to access the DNA:")
        self.write(mod_index)

    def menu(self):
        self.write("")
        self.write("You can:")
        self.write(" 1. Create your own Dino")
        self.write(" 2. View all available dinos")
        self.write(" 3. Download the DNA of a dino")
        self.write(" 4. Exit")

    def welcome(self):
        self.write("Hello and welcome to the")
        self.banner()
        self.write("")
        self.write("Here, you can give us your 🦕 and we extract and store DNA samples for all your cloning needs.")
        self.write("Make sure to back up your creations before the next apocalypse!")

    def banner(self):
        self.write("""
🌋🌋🌋🌋🌋🦕🦕🦕🌋🌋🌋🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🦕🌋🌋🌋🦕🦕🦕🦕🌋🌋🌋🦕🦕🦕🦕🦕🌋🌋🦕🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🌋🌋🌋🦕
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🌋🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🌋🌋🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🌋🌋🌋🦕
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🦕🦕🦕🌋🦕🦕🌋🌋🌋🌋🌋🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🌋🦕🦕🦕
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🌋🦕🦕
🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🌋🦕🦕🦕🌋🦕🦕🌋🦕🦕🌋🦕
🌋🌋🌋🌋🌋🦕🦕🦕🌋🌋🌋🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🦕🌋🌋🌋🦕🦕🦕🦕🌋🌋🌋🦕🦕🦕🌋🦕🦕🦕🦕🌋🦕🦕🦕🌋🌋🌋🦕🦕🦕🌋🦕🦕🦕🌋
                   """)
        self.write("Vault")

    def handle_choice(self, choice):
        match choice:
            case 1:
                self.create()
                return True
            case 2:
                self.view()
                return True
            case 3:
                self.download()
                return True
            case 4:
                self.write("See you soon at the")
                self.banner()
                return False
            case _:
                self.menu()
                return True

    def handle(self):
        self.prepare_dinos()
        self.banner()
        self.menu()

        choice = self.read_int()
        while self.handle_choice(choice):
            self.write("What do you want to do now?")
            choice = self.read_int()
        

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 5000
    with socketserver.ThreadingTCPServer((HOST, PORT), DinoVaultServer) as server:
        server.serve_forever()
