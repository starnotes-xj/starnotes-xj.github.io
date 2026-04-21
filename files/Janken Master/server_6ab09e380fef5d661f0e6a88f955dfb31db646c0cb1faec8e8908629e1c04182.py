#!/usr/local/bin/python3
import os


class Xoroshiro128Plus:
    MASK = 0xFFFFFFFFFFFFFFFF

    def __init__(self, seed):

        self.s = [seed >> 64 & self.MASK, seed & self.MASK]

    def rotl(self, x, k):
        return ((x << k) | (x >> (64 - k))) & self.MASK

    def next(self):
        s0 = self.s[0]
        s1 = self.s[1]

        result = (self.rotl((s0 + s1) & self.MASK, 17) + s0) & self.MASK
        s1 ^= s0
        self.s[0] = (self.rotl(s0, 49) ^ s1 ^ (
            (s1 << 21) & self.MASK)) & self.MASK
        self.s[1] = self.rotl(s1, 28)

        return result


def main():
    FLAG = os.environ.get("FLAG", "FLAG{DUMMY}")
    NPC_COUNT = 99

    print("=====================================================")
    print(f" Welcome to the {NPC_COUNT + 1}-Player Rock-Paper-Scissors! ")
    print(" Can you become the sole winner against all NPCs?")
    print("=====================================================\n")

    try:
        seed_input = input("Enter your lucky number (seed): ")
        seed = int(seed_input)
    except ValueError:
        print("Invalid input. Please enter an integer.")
        return

    seed ^= 0x1234567890abcdef1234567890abcdef
    rng = Xoroshiro128Plus(seed)

    print("\nSelect your hand:")
    print("0: Rock (グー)")
    print("1: Scissors (チョキ)")
    print("2: Paper (パー)")

    try:
        player_hand = int(input("Your hand (0-2): "))
        if player_hand not in [0, 1, 2]:
            print("Invalid hand.")
            return
    except ValueError:
        print("Invalid input.")
        return

    npc_hands = []
    for _ in range(NPC_COUNT):
        npc_hands.append(rng.next() % 3)
    rock_count = npc_hands.count(0)
    scissors_count = npc_hands.count(1)
    paper_count = npc_hands.count(2)

    print("\n--- Result ---")
    print(f"Your hand: {player_hand}")
    print(
        f"NPC hands: Rock={rock_count}, Scissors={scissors_count}, Paper={paper_count}")

    # 勝敗判定
    hands_in_field = set(npc_hands)
    hands_in_field.add(player_hand)

    if len(hands_in_field) == 3:
        print("\nDraw! All three hands appeared in the field.")
    elif len(hands_in_field) == 1:
        print("\nDraw! Everyone played the same hand.")
    else:
        if (player_hand == 0 and 1 in hands_in_field) or \
           (player_hand == 1 and 2 in hands_in_field) or \
           (player_hand == 2 and 0 in hands_in_field):
            winner_count = 1 + npc_hands.count(player_hand)
            if winner_count == 1:
                print("\nCongratulations! You are the SOLE winner!")
                print(f"Here is your reward: {FLAG}")
            else:
                print(
                    f"\nYou won! But there are {winner_count} winners in total.")
                print("You must be the *sole* winner to get the flag.")
        else:
            print("\nYou lost...")


if __name__ == "__main__":
    main()
