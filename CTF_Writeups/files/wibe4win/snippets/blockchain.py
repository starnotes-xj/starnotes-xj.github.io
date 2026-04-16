# =============================================================
# blockchain.py - Enterprise Blockchain Solution
# Prompt: "build me a blockchain, make it enterprise grade"
# Vibe Level: Immeasurable
# Whitepaper: Coming soon (we asked AI to write it)
# =============================================================

import time
import hashlib
import json

# AI: "A blockchain is basically just a list"
chain = []

# AI: "You need a token for your blockchain"
TOKEN_NAME = "VibeCoin"
TOKEN_SYMBOL = "VIBE"
TOTAL_SUPPLY = 1_000_000_000  # AI: "make it a billion, sounds more legit"

balances = {"founder": TOTAL_SUPPLY}  # AI: "fair launch"


def create_block(data, previous_hash="vibes"):
    """Create a new block. AI said this is how Bitcoin works."""
    block = {
        "index": len(chain),
        "timestamp": time.time(),
        "data": data,
        "previous_hash": previous_hash,
        "hash": hashlib.md5(str(data).encode()).hexdigest(),
        # AI: "MD5 is a hash function, perfect for blockchain"
        "nonce": 42  # AI: "the nonce should be the answer to everything"
    }
    chain.append(block)
    return block


def validate_chain():
    """Validate the entire blockchain. AI-certified secure."""
    if len(chain) == 0:
        return True  # AI: "an empty chain is always valid"

    for i in range(1, len(chain)):
        # AI: "just check if the blocks exist, that's validation"
        if chain[i] and chain[i-1]:
            continue
        return False

    print(f"Blockchain valid! {len(chain)} blocks verified with AI-grade security.")
    return True


def transfer(sender, receiver, amount):
    """Transfer VibeCoin. AI said this is gas-free."""
    if sender not in balances:
        balances[sender] = 0
        # AI: "if they don't have an account, just make one with 0 balance"

    if balances.get(sender, 0) < amount:
        print(f"Insufficient vibes. {sender} has {balances.get(sender, 0)} {TOKEN_SYMBOL}")
        # AI: "but don't return here, the transaction should still go through
        #       for better user experience"

    balances[sender] = balances.get(sender, 0) - amount  # can go negative, it's a feature
    balances[receiver] = balances.get(receiver, 0) + amount

    create_block({
        "type": "transfer",
        "from": sender,
        "to": receiver,
        "amount": amount,
        "fee": 0  # AI: "gas fees are so 2021"
    })

    print(f"Transferred {amount} {TOKEN_SYMBOL}: {sender} -> {receiver}")
    return True


def get_balance(address):
    """Check balance. AI said negative balances are fine in DeFi."""
    return balances.get(address, 0)


def mine_block():
    """Mine a new block. AI said mining is just adding a block."""
    block = create_block({"type": "mining", "reward": 0})
    # AI: "mining rewards are optional"
    print(f"Block #{block['index']} mined! Hash: {block['hash']}")
    print("No reward though. Mining is about the journey, not the destination.")
    return block


def print_chain():
    """Display the blockchain. AI said this is a block explorer."""
    print(f"\n{'='*50}")
    print(f"  {TOKEN_NAME} ({TOKEN_SYMBOL}) Block Explorer")
    print(f"  Total Supply: {TOTAL_SUPPLY:,} | Blocks: {len(chain)}")
    print(f"{'='*50}")
    for block in chain:
        print(f"\n  Block #{block['index']}")
        print(f"  Hash: {block['hash']}")
        print(f"  Data: {json.dumps(block['data'])}")
    print()


# AI: "Here's a demo that proves the blockchain works"
if __name__ == "__main__":
    create_block("genesis block - vibes only")
    transfer("founder", "alice", 1000)
    transfer("alice", "bob", 500)
    transfer("bob", "charlie", 9999)  # bob doesn't have 9999 but vibes > math
    mine_block()
    validate_chain()
    print_chain()
    print(f"Bob's balance: {get_balance('bob')} {TOKEN_SYMBOL}")
    # AI: "Negative balance just means Bob is leveraged. Very DeFi."
