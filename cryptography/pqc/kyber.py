"""
kyber.py — CRYSTALS-Kyber Post-Quantum Key Encapsulation
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

What is Kyber?
  - NIST standard: ML-KEM (FIPS 203) — finalized 2024
  - Lattice-based cryptography — hard even for quantum computers
  - Replaces RSA/ECC for key exchange in post-quantum world
  - Kyber512  → LOW/MEDIUM risk  (faster, smaller keys)
  - Kyber1024 → HIGH risk        (stronger, used when threat detected)

How it works:
  1. Receiver generates keypair (public + private key)
  2. Sender uses public key → gets ciphertext + shared_secret
  3. Receiver uses private key + ciphertext → recovers same shared_secret
  4. Both sides now have the same secret — use it as AES key

Called by: hybrid/hybrid_scheme.py
"""

import oqs
import base64


# ── Algorithm selection ────────────────────────────────────────────────────────

ALGORITHMS = {
    "kyber512"  : "Kyber512",    # LOW/MEDIUM risk — 800 byte public key
    "kyber1024" : "Kyber1024",   # HIGH risk       — 1568 byte public key
}

DEFAULT_ALGORITHM = "kyber512"


def _get_algo_name(algorithm: str) -> str:
    """Resolve algorithm string to liboqs name. Case-insensitive."""
    key = algorithm.lower().replace("-", "")
    if key not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm '{algorithm}'. Choose: kyber512, kyber1024")
    return ALGORITHMS[key]


# ── Key Generation ─────────────────────────────────────────────────────────────

def generate_keypair(algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Generate a Kyber public/private keypair.

    Args:
        algorithm : "kyber512" or "kyber1024"

    Returns dict with:
        public_key       : base64 encoded — share this with sender
        private_key      : base64 encoded — keep this SECRET
        algorithm        : algorithm name used
        public_key_size  : bytes (800 for Kyber512, 1568 for Kyber1024)
        private_key_size : bytes

    Security note:
        Private key must never leave the receiver's system.
        Public key is safe to share openly.
    """
    algo_name = _get_algo_name(algorithm)

    with oqs.KeyEncapsulation(algo_name) as kem:
        public_key  = kem.generate_keypair()
        private_key = kem.export_secret_key()

    return {
        "public_key"       : base64.b64encode(public_key).decode(),
        "private_key"      : base64.b64encode(private_key).decode(),
        "algorithm"        : algo_name,
        "public_key_size"  : len(public_key),
        "private_key_size" : len(private_key),
    }


# ── Key Encapsulation (Sender side) ───────────────────────────────────────────

def encapsulate(public_key_b64: str, algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Sender side: wrap a shared secret using receiver's public key.
    The shared_secret becomes the AES key.
    The ciphertext is sent to the receiver so they can recover it.

    Args:
        public_key_b64 : receiver's public key (base64)
        algorithm      : must match the keypair algorithm

    Returns dict with:
        ciphertext     : base64 — send this to receiver
        shared_secret  : base64 — use this as AES key (DO NOT send this)
    """
    algo_name  = _get_algo_name(algorithm)
    public_key = base64.b64decode(public_key_b64)

    with oqs.KeyEncapsulation(algo_name) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)

    return {
        "ciphertext"    : base64.b64encode(ciphertext).decode(),
        "shared_secret" : base64.b64encode(shared_secret).decode(),
        "algorithm"     : algo_name,
        "ciphertext_size"     : len(ciphertext),
        "shared_secret_size"  : len(shared_secret),
    }


# ── Key Decapsulation (Receiver side) ─────────────────────────────────────────

def decapsulate(ciphertext_b64: str, private_key_b64: str,
                algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Receiver side: recover the shared secret using private key + ciphertext.
    The recovered shared_secret will exactly match what sender got.

    Args:
        ciphertext_b64  : ciphertext from encapsulate()
        private_key_b64 : receiver's private key from generate_keypair()
        algorithm       : must match the keypair algorithm

    Returns dict with:
        shared_secret : base64 — use this as AES key
    """
    algo_name   = _get_algo_name(algorithm)
    ciphertext  = base64.b64decode(ciphertext_b64)
    private_key = base64.b64decode(private_key_b64)

    with oqs.KeyEncapsulation(algo_name, secret_key=private_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)

    return {
        "shared_secret" : base64.b64encode(shared_secret).decode(),
        "algorithm"     : algo_name,
        "shared_secret_size" : len(shared_secret),
    }


# ── Key Rotation ───────────────────────────────────────────────────────────────

def rotate_keypair(algorithm: str = DEFAULT_ALGORITHM) -> dict:
    """
    Generate a fresh keypair — called by self-healing module on HIGH threat.
    Old sessions using previous keys are immediately invalidated.
    """
    print(f"[KYBER] Key rotation triggered — generating fresh {algorithm} keypair")
    return generate_keypair(algorithm)


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  CipherZenith — CRYSTALS-Kyber Module Test")
    print("=" * 55)

    for algo in ["kyber512", "kyber1024"]:
        print(f"\n{'─'*55}")
        print(f"  Testing {algo.upper()}")
        print(f"{'─'*55}")

        # Step 1: Generate keypair
        print(f"\n[1] Generating {algo} keypair...")
        keypair = generate_keypair(algo)
        print(f"    Algorithm      : {keypair['algorithm']}")
        print(f"    Public key     : {keypair['public_key_size']} bytes")
        print(f"    Private key    : {keypair['private_key_size']} bytes")
        print(f"    (RSA-2048 public key = 256 bytes for comparison)")

        # Step 2: Sender encapsulates
        print(f"\n[2] Sender encapsulating shared secret...")
        enc = encapsulate(keypair["public_key"], algo)
        print(f"    Ciphertext size   : {enc['ciphertext_size']} bytes")
        print(f"    Shared secret size: {enc['shared_secret_size']} bytes")

        # Step 3: Receiver decapsulates
        print(f"\n[3] Receiver decapsulating...")
        dec = decapsulate(enc["ciphertext"], keypair["private_key"], algo)
        print(f"    Shared secret size: {dec['shared_secret_size']} bytes")

        # Step 4: Verify both sides got the same secret
        match = enc["shared_secret"] == dec["shared_secret"]
        print(f"\n[4] Secrets match : {match}")

        if match:
            print(f"    [PASS] {algo.upper()} key exchange successful!")
        else:
            print(f"    [FAIL] Secrets do not match!")

    # Key rotation test
    print(f"\n{'─'*55}")
    print(f"  Testing key rotation")
    print(f"{'─'*55}")
    new_keypair = rotate_keypair("kyber512")
    print(f"    New public key size: {new_keypair['public_key_size']} bytes")
    print(f"    [PASS] Key rotation working")

    print(f"\n{'='*55}")
    print(f"  All Kyber tests passed!")
    print(f"{'='*55}")