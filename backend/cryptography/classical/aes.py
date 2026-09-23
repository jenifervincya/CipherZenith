"""
aes.py — AES-256-GCM Encryption Module
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

Why AES-256-GCM?
  - AES-256  : 256-bit key — even Grover's quantum algorithm leaves it secure
  - GCM mode : Galois/Counter Mode — gives BOTH encryption AND authentication
              (detects if anyone tampered with the ciphertext)
  - No PKCS7 padding needed — GCM is a stream mode, handles any data size

Called by: hybrid/hybrid_scheme.py
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ── Key Generation ─────────────────────────────────────────────────────────────

def generate_key() -> bytes:
    """
    Generate a cryptographically secure random 256-bit (32 byte) AES key.
    Uses os.urandom() — pulls from the OS entropy pool, safe for crypto use.
    """
    return os.urandom(32)  # 32 bytes × 8 = 256 bits


def derive_key_from_secret(secret: bytes) -> bytes:
    """
    Convert any bytes (e.g. Kyber shared secret) into exactly 32 bytes.
    SHA-256 always outputs 32 bytes regardless of input size.
    Used when Kyber provides the key material instead of random generation.
    """
    return hashlib.sha256(secret).digest()


# ── Encryption ─────────────────────────────────────────────────────────────────

def encrypt(plaintext: str, key: bytes = None) -> dict:
    """
    Encrypt a plaintext string using AES-256-GCM.

    Args:
        plaintext : the data to encrypt (transaction JSON as string)
        key       : 32-byte AES key — if None, a fresh key is generated

    Returns dict with:
        ciphertext  : base64 encoded encrypted data (includes GCM auth tag)
        nonce       : base64 encoded 12-byte random nonce (never reuse!)
        key_b64     : base64 encoded key (Kyber will protect this)
        key_size    : always 256
        mode        : "AES-256-GCM"

    How it works:
        1. Generate random 12-byte nonce (unique per message)
        2. AES-256-GCM encrypts plaintext using key + nonce
        3. GCM automatically appends a 16-byte authentication tag
        4. Returns ciphertext (data + tag) + nonce for decryption
    """
    if key is None:
        key = generate_key()

    # Nonce: 12 bytes (96 bits) — MUST be unique for every encryption
    # Never reuse the same nonce with the same key — security catastrophe
    nonce = os.urandom(12)

    aesgcm = AESGCM(key)
    ciphertext_bytes = aesgcm.encrypt(
        nonce,
        plaintext.encode("utf-8"),
        None    # Additional Authenticated Data — None for now
    )

    return {
        "ciphertext" : base64.b64encode(ciphertext_bytes).decode("utf-8"),
        "nonce"      : base64.b64encode(nonce).decode("utf-8"),
        "key_b64"    : base64.b64encode(key).decode("utf-8"),
        "key_size"   : 256,
        "mode"       : "AES-256-GCM",
    }


# ── Decryption ─────────────────────────────────────────────────────────────────

def decrypt(ciphertext_b64: str, nonce_b64: str, key_b64: str) -> dict:
    """
    Decrypt AES-256-GCM ciphertext back to plaintext.

    Args:
        ciphertext_b64 : base64 encoded ciphertext (from encrypt())
        nonce_b64      : base64 encoded nonce (from encrypt())
        key_b64        : base64 encoded key (from encrypt())

    Returns dict with:
        success   : True if decryption worked
        plaintext : the original string (if success)
        tampered  : True if authentication tag failed (data was modified)

    GCM authentication:
        If even one byte of the ciphertext was changed after encryption,
        AESGCM.decrypt() raises InvalidTag exception.
        We catch this and return tampered=True.
        This is the authentication part of AES-256-GCM.
    """
    key        = base64.b64decode(key_b64)
    nonce      = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    aesgcm = AESGCM(key)

    try:
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return {
            "success"   : True,
            "plaintext" : plaintext_bytes.decode("utf-8"),
            "tampered"  : False,
        }
    except Exception:
        # GCM tag verification failed — ciphertext was tampered with
        return {
            "success"   : False,
            "plaintext" : None,
            "tampered"  : True,
            "error"     : "Authentication failed — data may have been tampered with",
        }


# ── Quick self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 55)
    print("  CipherZenith — AES-256-GCM Module Test")
    print("=" * 55)

    # Simulate a real transaction
    transaction = {
        "sender"   : "Jeni",
        "receiver" : "Mugunthan",
        "amount"   : 500,
        "txn_id"   : "TXN-20240622-001"
    }
    plaintext = json.dumps(transaction)

    print(f"\n[1] Original transaction:")
    print(f"    {plaintext}")

    # Encrypt
    print(f"\n[2] Encrypting with AES-256-GCM...")
    enc = encrypt(plaintext)
    print(f"    Ciphertext : {enc['ciphertext'][:40]}...")
    print(f"    Nonce      : {enc['nonce']}")
    print(f"    Key size   : {enc['key_size']} bits")
    print(f"    Mode       : {enc['mode']}")

    # Decrypt
    print(f"\n[3] Decrypting...")
    dec = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])
    print(f"    Recovered  : {dec['plaintext']}")
    print(f"    Tampered   : {dec['tampered']}")
    print(f"    Match      : {dec['plaintext'] == plaintext}")

    # Tamper test — change one character of ciphertext
    print(f"\n[4] Tamper test — modifying ciphertext...")
    bad_ct = enc["ciphertext"][:-4] + "XXXX"
    bad    = decrypt(bad_ct, enc["nonce"], enc["key_b64"])
    print(f"    Tampered   : {bad['tampered']}")
    print(f"    Error      : {bad.get('error')}")

    # Key size check
    print(f"\n[5] Key generation test...")
    k1 = generate_key()
    k2 = generate_key()
    print(f"    Key 1 size : {len(k1)} bytes ({len(k1)*8} bits)")
    print(f"    Keys same  : {k1 == k2}  ← must be False (random)")

    print(f"\n{'[PASS] AES-256-GCM working correctly!' if dec['plaintext'] == plaintext and bad['tampered'] else '[FAIL] Something went wrong'}")
    print("=" * 55)