"""
demo_sender.py - plays the SENDER in the CipherZenith demo.

The sender holds the private key and signs. The server only has the public
key (backend/trusted_keys.json), so it can verify but cannot forge.

Run from the repo root:
  python tests/manual/demo_sender.py init
  python tests/manual/demo_sender.py send --amount 50000
  python tests/manual/demo_sender.py send --amount 50000 --tamper
  python tests/manual/demo_sender.py send --amount 50000 --replay
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "cryptography", "pqc"))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

import dilithium                                  # noqa: E402  (Mugunthan's module)
from crypto.signing import canonical_message      # noqa: E402  (same function the server uses)

SENDER = "Jeni"
RECEIVER = "Mugunthan"
ALGORITHM = "dilithium2"   # ML-DSA-44
PRIVATE_KEY_FILE = os.path.join(REPO_ROOT, "tests", "manual", ".demo_private_key.json")
TRUSTED_KEYS_FILE = os.path.join(REPO_ROOT, "backend", "trusted_keys.json")
URL = "http://127.0.0.1:8000/api/transaction"


def init():
    if os.path.exists(PRIVATE_KEY_FILE):
        print("Private key already exists, not overwriting.")
        print("Delete", PRIVATE_KEY_FILE, "first if you want to rotate it.")
        return

    keypair = dilithium.generate_signing_keypair(ALGORITHM)

    with open(PRIVATE_KEY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "sender": SENDER,
                "algorithm": keypair["algorithm"],
                "private_key": keypair["private_key"],
            },
            f,
        )

    trusted = {}
    if os.path.exists(TRUSTED_KEYS_FILE):
        with open(TRUSTED_KEYS_FILE, encoding="utf-8") as f:
            trusted = json.load(f)
    trusted[SENDER] = {
        "algorithm": keypair["algorithm"],
        "public_key": keypair["public_key"],
    }
    with open(TRUSTED_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(trusted, f, indent=2)

    print("Keypair created for", SENDER, "using", keypair["algorithm"])
    print("  private key ->", PRIVATE_KEY_FILE, "(secret, git-ignored)")
    print("  public key  ->", TRUSTED_KEYS_FILE, "(safe to commit)")


def post(body):
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            print("  HTTP", response.status, response.read().decode())
    except urllib.error.HTTPError as e:
        print("  HTTP", e.code, e.read().decode())


def send(amount, tamper, replay):
    if not os.path.exists(PRIVATE_KEY_FILE):
        print("No private key found. Run: python tests/manual/demo_sender.py init")
        return

    with open(PRIVATE_KEY_FILE, encoding="utf-8") as f:
        key = json.load(f)

    timestamp = time.time()
    nonce = "n-" + uuid.uuid4().hex[:12]

    # Sign the real transaction
    message = canonical_message(SENDER, RECEIVER, amount, nonce, timestamp)
    signature = dilithium.sign(message, key["private_key"], key["algorithm"])["signature"]

    # --tamper: an attacker changes the amount after it was signed
    sent_amount = amount * 10 if tamper else amount

    body = {
        "sender": SENDER,
        "receiver": RECEIVER,
        "amount": float(sent_amount),
        "nonce": nonce,
        "timestamp": timestamp,
        "signature": signature,
    }

    attempts = 2 if replay else 1
    for i in range(attempts):
        label = "sending" if i == 0 else "replaying the identical request"
        print(f"{label}: amount={sent_amount}, nonce={nonce}")
        post(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create the sender keypair")
    send_parser = sub.add_parser("send", help="send a signed transaction")
    send_parser.add_argument("--amount", type=float, default=50000)
    send_parser.add_argument("--tamper", action="store_true")
    send_parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()

    if args.command == "init":
        init()
    else:
        send(args.amount, args.tamper, args.replay)
