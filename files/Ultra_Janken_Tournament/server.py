#!/usr/local/bin/python3
from random import randrange
from os import getenv


def nextrand(n):
    n ^= n << 13
    n ^= n >> 7
    n ^= n << 17
    return n & ((1 << 64) - 1)


def main():
    MAX_CHEAT_COUNT = 600
    PARTICIPANTS = 101
    STRATEGY_LEN = 120
    MATCHES = 20

    janken_powers = [[0 for _ in range(STRATEGY_LEN)]
                     for _ in range(PARTICIPANTS - 1)]

    for i in range(PARTICIPANTS - 1):
        janken_powers[i][0] = randrange(1, 2**64)
        for j in range(1, STRATEGY_LEN):
            janken_powers[i][j] = nextrand(janken_powers[i][j - 1])

    print("🌟====================================================🌟")
    print("  ✊✌️✋ Welcome to the ULTRA JANKEN TOURNAMENT! ✋✌️✊")
    print("🌟====================================================🌟")
    print("\n[MC] First, tell me your \"Secret Janken Strategy\"! (Space-separated integers, please!)")

    try:
        player_strategy = list(map(int, input("Your Strategy: ").split()))
    except ValueError:
        print("[MC] Oops! Those don't look like numbers. Please try again!")
        exit(0)

    assert len(player_strategy) == STRATEGY_LEN
    for val in player_strategy:
        assert 0 <= val < 2**64

    print(f"\n[MC] Entry complete! We've received your strategy loud and clear!")
    janken_powers.append(player_strategy)

    total_cheats = 0

    print("\n[MC] Now, let the tournament of destiny BEGIN!!!\n")

    for match_num in range(MATCHES):
        print(f"\n--- [ MATCH {match_num + 1}/{MATCHES} ] ---")
        player_no = randrange(0, PARTICIPANTS)
        luck_pattern = [randrange(0, 2) for _ in range(STRATEGY_LEN)]

        print(f"[MC] Your Number is No: {player_no}")
        lucky = "".join(map(str, luck_pattern))
        print(f"[info] Current Luck Pattern: {lucky}")

        while True:
            action = input(
                "\n[?] What will you do? [C]heat the luck / [G]o Janken!: ").strip().upper()

            if action == "C":
                try:
                    idx = int(input("Which luck index to flip?: "))
                    if 0 <= idx < STRATEGY_LEN:
                        luck_pattern[idx] = 1 - luck_pattern[idx]
                        total_cheats += 1
                        print("[Info] Luck value altered silently.")
                    else:
                        print("[ERROR] Error: Index out of range.")
                except ValueError:
                    print("[ERROR] Error: Invalid integer.")

            elif action == "G":
                break
            else:
                print("[ERROR] Unrecognized command.")
                exit(0)

        clash_power = 0
        for i in range(PARTICIPANTS):
            for j in range(STRATEGY_LEN):
                clash_power ^= janken_powers[i][j] * luck_pattern[j]

        winner = clash_power % PARTICIPANTS

        print(
            "\n[MC] Alright, everyone together... Rock, Paper, SCISSORS!!! ✊✌️✋")
        print(f"[MC] And the winner is... Participant No.{winner}!!!")

        if winner != player_no:
            print("\n[Info] You lost...")
            exit(0)

        if total_cheats > MAX_CHEAT_COUNT:
            print(
                "\n[MC] Wait a minute... the luck generators are fluctuating wildly! SECURITY!!")
            exit(0)

        print("[MC] What an incredible match! Let's move right to the next one!\n")

    print("🎊======================================================🎊")
    print("  🏆 TOURNAMENT COMPLETED! 🏆")
    print("🎊======================================================🎊")
    print("\n[MC] What a breathtaking tournament! I've never seen such consistent \"luck\" before!")
    print("[MC] Please accept this grand prize on behalf of our amazing winner! \n")

    flag = getenv("FLAG", "FLAG{DUMMY}")
    print(flag)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[MC] Whoops! Looks like we have some technical difficulties!")
