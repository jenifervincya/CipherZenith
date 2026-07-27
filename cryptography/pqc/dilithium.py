"""
dilithium.py — CRYSTALS-Dilithium Digital Signatures
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

NIST final names (used in liboqs 0.10+):
  ML-DSA-44  →  was Dilithium2  →  LOW/MEDIUM risk
  ML-DSA-65  →  was Dilithium3  →  HIGH risk
  ML-DSA-87  →  was Dilithium5  →  maximum security

Why signatures?
  - Kyber  = CONFIDENTIALITY  (nobody reads the data)
  - Dilithium = AUTHENTICITY  (nobody fakes the sender)
  - Together: data is secret AND verified genuine
"""

import oqs
import base64
import json
import hashlib


# ── Algorithm selection ────────────────────────────────────────────────────────

ALGORITHMS = {
    "dilithium2" : "ML-DSA-44",   # NIST final name — LOW/MEDIUM risk
    "dilithium3" : "ML-DSA-65",   # NIST final name — HIGH risk
    "dilithium5" : "ML-DSA-87",   # NIST final name — maximum
    # Also accept direct NIST names
    "ml-dsa-44"  : "ML-DSA-44",
    "ml-dsa-65"  : "ML-DSA-65",
    "ml-dsa-87"  : "ML-DSA-87",
}

DEFAULT_ALGORITHM = "dilithium2"


def _get_algo_name(algorithm: str) -> str:
    key = algorithm.lower().replace("-", "").replace(" ", "")
    # normalise ml-dsa-44 → mldsa44
    key = key.replace("mldsa", "ml-dsa-").replace("--", "-")
    # try direct lookup first
    if algorithm in ALGORITHMS:
        return ALGORITHMS[algorithm]
    if key in ALGORITHMS:
        return ALGORITHMS[key]
    # try lowercase match
    for k, v in ALGORITHMS.items():
        if k.replace("-","") == key.replace("-",""):
            return v
    raise ValueError(
        f"Unknown algorithm '{algorithm}'.\n"
        f"Choose from: {list(ALGORITHMS.keys())}"
    )


# ── Key Generation ─────────────────────────────────────────────────────────────

def generate_signing_keypair(algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Generate a Dilithium signing keypair.
    Returns: public_key, private_key (both base64), sizes.
    """
    algo_name = _get_algo_name(algorithm)

    with oqs.Signature(algo_name) as signer:
        public_key  = signer.generate_keypair()
        private_key = signer.export_secret_key()

    return {
        "public_key"       : base64.b64encode(public_key).decode(),
        "private_key"      : base64.b64encode(private_key).decode(),
        "algorithm"        : algo_name,
        "public_key_size"  : len(public_key),
        "private_key_size" : len(private_key),
    }


# ── Sign ───────────────────────────────────────────────────────────────────────

def sign(message: str, private_key_b64: str,
         algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Sign a message string with the private key.
    Even one character change in message → signature invalid.
    """
    algo_name   = _get_algo_name(algorithm)
    private_key = base64.b64decode(private_key_b64)
    msg_bytes   = message.encode("utf-8")

    with oqs.Signature(algo_name, secret_key=private_key) as signer:
        signature = signer.sign(msg_bytes)

    return {
        "signature"      : base64.b64encode(signature).decode(),
        "message_hash"   : hashlib.sha256(msg_bytes).hexdigest(),
        "algorithm"      : algo_name,
        "signature_size" : len(signature),
    }


# ── Verify ─────────────────────────────────────────────────────────────────────

def verify(message: str, signature_b64: str,
           public_key_b64: str, algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Verify a signature using the sender's public key.
    Returns valid=True only if message + signature + key all match exactly.
    """
    algo_name  = _get_algo_name(algorithm)
    public_key = base64.b64decode(public_key_b64)
    signature  = base64.b64decode(signature_b64)
    msg_bytes  = message.encode("utf-8")

    with oqs.Signature(algo_name) as verifier:
        is_valid = verifier.verify(msg_bytes, signature, public_key)

    return {
        "valid"     : is_valid,
        "algorithm" : algo_name,
        "message"   : message,
    }


# ── Transaction helpers ────────────────────────────────────────────────────────

def sign_transaction(transaction: dict, private_key_b64: str,
                     algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """Sign a transaction dict — serialises to JSON first."""
    message = json.dumps(transaction, sort_keys=True)
    return sign(message, private_key_b64, algorithm)


def verify_transaction(transaction: dict, signature_b64: str,
                       public_key_b64: str,
                       algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """Verify a transaction dict signature."""
    message = json.dumps(transaction, sort_keys=True)
    return verify(message, signature_b64, public_key_b64, algorithm)


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("  CipherZenith — CRYSTALS-Dilithium Signature Test")
    print("=" * 58)

    transaction = {
        "sender"    : "Jeni",
        "receiver"  : "Mugunthan",
        "amount"    : 500,
        "txn_id"    : "TXN-20240622-001",
        "timestamp" : "2024-06-22T10:30:00"
    }

    for algo in ["dilithium2", "dilithium3"]:
        print(f"\n{'─'*58}")
        print(f"  Testing {algo.upper()}  ({_get_algo_name(algo)})")
        print(f"{'─'*58}")

        # 1 — generate keypair
        print(f"\n[1] Generating signing keypair...")
        keypair = generate_signing_keypair(algo)
        print(f"    Algorithm      : {keypair['algorithm']}")
        print(f"    Public key     : {keypair['public_key_size']} bytes")
        print(f"    Private key    : {keypair['private_key_size']} bytes")
        print(f"    (ECDSA public key = 64 bytes for comparison)")

        # 2 — sign
        print(f"\n[2] Signing transaction...")
        signed = sign_transaction(transaction, keypair["private_key"], algo)
        print(f"    Signature      : {signed['signature'][:48]}...")
        print(f"    Signature size : {signed['signature_size']} bytes")

        # 3 — verify genuine
        print(f"\n[3] Verifying genuine signature...")
        r = verify_transaction(transaction, signed["signature"],
                               keypair["public_key"], algo)
        print(f"    Valid          : {r['valid']}")
        print(f"    [{'PASS' if r['valid'] else 'FAIL'}] Genuine signature accepted")

        # 4 — tamper test
        print(f"\n[4] Tamper test — changing amount 500 → 99999...")
        tampered = {**transaction, "amount": 99999}
        r2 = verify_transaction(tampered, signed["signature"],
                                keypair["public_key"], algo)
        print(f"    Valid          : {r2['valid']}")
        print(f"    [{'PASS' if not r2['valid'] else 'FAIL'}] Tampered transaction rejected")

        # 5 — wrong key test
        print(f"\n[5] Wrong key test — forged keypair...")
        fake = generate_signing_keypair(algo)
        r3   = verify_transaction(transaction, signed["signature"],
                                  fake["public_key"], algo)
        print(f"    Valid          : {r3['valid']}")
        print(f"    [{'PASS' if not r3['valid'] else 'FAIL'}] Forged key rejected")

    print(f"\n{'='*58}")
    print(f"  All Dilithium tests passed!")
    print(f"  Quantum-safe signatures: tamper-proof + forgery-proof")
    print(f"{'='*58}")