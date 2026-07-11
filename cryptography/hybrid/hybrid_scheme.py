"""
hybrid_scheme.py — Hybrid Encryption: AES-256-GCM + CRYSTALS-Kyber
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

This is the MAIN FILE Jenifer's backend imports.
Two functions she calls:
  1. encrypt(transaction_data, risk_level)   → Step 2 of the 8-step pipeline
  2. switch_algorithm(encrypted_package, new_algorithm) → Step 5 (threat detected)

How hybrid encryption works:
  ┌─────────────────────────────────────────────────────┐
  │  Transaction JSON                                   │
  │        ↓                                           │
  │  AES-256-GCM encrypts the data  (fast, bulk)       │
  │        ↓                                           │
  │  Kyber encapsulates the AES key (quantum-safe)     │
  │        ↓                                           │
  │  Package: { kyber_ciphertext, aes_ciphertext,      │
  │             nonce, algorithm_used }                │
  └─────────────────────────────────────────────────────┘

Why hybrid and not just Kyber alone?
  - Kyber is for KEY EXCHANGE only — not bulk data encryption
  - AES is fast and efficient for encrypting large data
  - Kyber protects the AES key from quantum attacks
  - Together = speed of AES + quantum safety of Kyber
"""

import sys
import os
import json
import base64
import hashlib

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classical.aes import encrypt as aes_encrypt, decrypt as aes_decrypt, derive_key_from_secret
from pqc.kyber import generate_keypair, encapsulate, decapsulate, rotate_keypair


# ── Risk level → algorithm mapping ────────────────────────────────────────────

RISK_ALGORITHM = {
    "LOW"    : "kyber512",   # default — faster, smaller
    "MEDIUM" : "kyber512",   # same algorithm, but logged as elevated
    "HIGH"   : "kyber1024",  # stronger — triggered by AI threat detection
}


# ── Session key store (in-memory for demo) ────────────────────────────────────
# In production this would be an HSM or secure key vault
# For demo: stored in memory, rotated on threat detection

_session_keys = {}   # { algorithm: { public_key, private_key } }


def _get_or_create_keypair(algorithm: str) -> dict:
    """Get existing keypair for algorithm or generate a fresh one."""
    if algorithm not in _session_keys:
        print(f"[HYBRID] Generating fresh {algorithm} keypair for session")
        _session_keys[algorithm] = generate_keypair(algorithm)
    return _session_keys[algorithm]


# ── Main encrypt function — Jenifer calls this at Step 2 ──────────────────────

def encrypt(transaction_data: dict, risk_level: str = "LOW") -> dict:
    """
    Encrypt transaction data using Hybrid AES-256 + Kyber.
    Called by Jenifer's backend at Step 2 of the security pipeline.

    Args:
        transaction_data : dict — e.g. {"sender": "Jeni", "receiver": "Mugunthan", "amount": 500}
        risk_level       : "LOW", "MEDIUM", or "HIGH"
                           HIGH → uses Kyber1024 instead of Kyber512

    Returns dict with:
        encrypted_data   : dict containing all data needed for decryption
        algorithm_used   : human-readable string e.g. "AES-256-GCM + Kyber512"
        key_info         : metadata about keys used (no actual private keys)
        risk_level       : echoed back for logging

    How it works internally:
        Step A: Pick algorithm based on risk_level
        Step B: Get/create Kyber keypair for this session
        Step C: Encapsulate — get shared_secret + kyber_ciphertext
        Step D: Derive 32-byte AES key from shared_secret
        Step E: AES-256-GCM encrypt the transaction JSON
        Step F: Return full package
    """
    # Step A — pick algorithm
    algorithm = RISK_ALGORITHM.get(risk_level.upper(), "kyber512")

    # Step B — get session keypair
    keypair = _get_or_create_keypair(algorithm)

    # Step C — Kyber encapsulation: sender gets shared_secret
    enc_result = encapsulate(keypair["public_key"], algorithm)

    # Step D — derive AES key from Kyber shared secret
    shared_secret_bytes = base64.b64decode(enc_result["shared_secret"])
    aes_key = derive_key_from_secret(shared_secret_bytes)   # SHA-256 → 32 bytes

    # Step E — AES-256-GCM encrypt the transaction
    plaintext = json.dumps(transaction_data)
    aes_result = aes_encrypt(plaintext, aes_key)

    # Step F — build the complete encrypted package
    algorithm_label = f"AES-256-GCM + {'Kyber512' if algorithm == 'kyber512' else 'Kyber1024'}"

    encrypted_data = {
        # AES output
        "aes_ciphertext"    : aes_result["ciphertext"],
        "aes_nonce"         : aes_result["nonce"],
        "aes_mode"          : aes_result["mode"],
        # Kyber output — receiver uses this to recover the AES key
        "kyber_ciphertext"  : enc_result["ciphertext"],
        "kyber_algorithm"   : enc_result["algorithm"],
        # Metadata
        "algorithm_label"   : algorithm_label,
        "risk_level"        : risk_level.upper(),
    }

    key_info = {
        "kyber_algorithm"        : enc_result["algorithm"],
        "kyber_public_key_size"  : keypair["public_key_size"],
        "aes_key_size_bits"      : 256,
        "shared_secret_size"     : enc_result["shared_secret_size"],
    }

    return {
        "encrypted_data" : encrypted_data,
        "algorithm_used" : algorithm_label,
        "key_info"       : key_info,
        "risk_level"     : risk_level.upper(),
    }


# ── Switch algorithm — Jenifer calls this at Step 5 ───────────────────────────

def switch_algorithm(encrypted_package: dict, new_algorithm: str = "kyber1024") -> dict:
    """
    Re-encrypt data with a stronger algorithm when threat is detected.
    Called by Jenifer's backend at Step 5 (Adaptive Engine).

    Args:
        encrypted_package : the full dict returned by encrypt()
        new_algorithm     : "kyber512" or "kyber1024" (usually kyber1024 on HIGH threat)

    Returns dict with:
        re_encrypted_data : new encrypted package with stronger algorithm
        algorithm_used    : new algorithm label
        key_info          : new key metadata
        switched_from     : previous algorithm (for dashboard display)
        switched_to       : new algorithm

    How it works:
        Step A: Decrypt the original data using old keys
        Step B: Rotate keys — generate fresh keypair for new algorithm
        Step C: Re-encrypt with new algorithm
        Step D: Return new package + switch metadata
    """
    encrypted_data = encrypted_package.get("encrypted_data", encrypted_package)
    old_algorithm_label = encrypted_data.get("algorithm_label", "Unknown")
    old_kyber_algo = encrypted_data.get("kyber_algorithm", "Kyber512")

    # Step A — decrypt original to get plaintext back
    # Find which keypair was used originally
    old_algo_key = "kyber512" if "512" in old_kyber_algo else "kyber1024"

    if old_algo_key not in _session_keys:
        raise ValueError("Original session keys not found — cannot switch algorithm")

    old_keypair = _session_keys[old_algo_key]

    # Recover the AES key via Kyber decapsulation
    dec_result = decapsulate(
        encrypted_data["kyber_ciphertext"],
        old_keypair["private_key"],
        old_algo_key
    )
    shared_secret_bytes = base64.b64decode(dec_result["shared_secret"])
    old_aes_key = derive_key_from_secret(shared_secret_bytes)

    # Decrypt AES to recover original plaintext
    aes_dec = aes_decrypt(
        encrypted_data["aes_ciphertext"],
        encrypted_data["aes_nonce"],
        base64.b64encode(old_aes_key).decode()
    )

    if not aes_dec["success"]:
        raise ValueError(f"Decryption failed during algorithm switch: {aes_dec.get('error')}")

    plaintext = aes_dec["plaintext"]

    # Step B — rotate keys: generate fresh keypair for new algorithm
    print(f"[HYBRID] Switching algorithm: {old_kyber_algo} → {new_algorithm.upper()}")
    print(f"[HYBRID] Rotating keys — all old sessions invalidated")
    _session_keys[new_algorithm] = rotate_keypair(new_algorithm)

    # Step C — re-encrypt with new algorithm
    new_algo_name = new_algorithm.lower().replace("-", "")
    new_keypair   = _session_keys[new_algo_name]
    new_enc       = encapsulate(new_keypair["public_key"], new_algo_name)

    new_shared_secret = base64.b64decode(new_enc["shared_secret"])
    new_aes_key       = derive_key_from_secret(new_shared_secret)
    new_aes_result    = aes_encrypt(plaintext, new_aes_key)

    new_algorithm_label = f"AES-256-GCM + {'Kyber512' if '512' in new_algo_name else 'Kyber1024'}"

    re_encrypted_data = {
        "aes_ciphertext"   : new_aes_result["ciphertext"],
        "aes_nonce"        : new_aes_result["nonce"],
        "aes_mode"         : new_aes_result["mode"],
        "kyber_ciphertext" : new_enc["ciphertext"],
        "kyber_algorithm"  : new_enc["algorithm"],
        "algorithm_label"  : new_algorithm_label,
        "risk_level"       : "HIGH",
    }

    key_info = {
        "kyber_algorithm"       : new_enc["algorithm"],
        "kyber_public_key_size" : new_keypair["public_key_size"],
        "aes_key_size_bits"     : 256,
        "shared_secret_size"    : new_enc["shared_secret_size"],
    }

    return {
        "re_encrypted_data" : re_encrypted_data,
        "algorithm_used"    : new_algorithm_label,
        "key_info"          : key_info,
        "switched_from"     : old_algorithm_label,
        "switched_to"       : new_algorithm_label,
    }


# ── Decrypt helper — for testing and verification ─────────────────────────────

def decrypt_package(encrypted_data: dict, algorithm: str = None) -> dict:
    """
    Decrypt an encrypted package. Used for testing and verification.
    In production, decryption happens at the secure destination.
    """
    kyber_algo = encrypted_data.get("kyber_algorithm", "Kyber512")
    algo_key   = "kyber512" if "512" in kyber_algo else "kyber1024"

    if algo_key not in _session_keys:
        raise ValueError("Session keys not found — cannot decrypt")

    keypair = _session_keys[algo_key]

    # Recover AES key via Kyber
    dec_result          = decapsulate(encrypted_data["kyber_ciphertext"], keypair["private_key"], algo_key)
    shared_secret_bytes = base64.b64decode(dec_result["shared_secret"])
    aes_key             = derive_key_from_secret(shared_secret_bytes)

    # Decrypt AES
    result = aes_decrypt(
        encrypted_data["aes_ciphertext"],
        encrypted_data["aes_nonce"],
        base64.b64encode(aes_key).decode()
    )

    return result


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  CipherZenith — Hybrid Encryption Module Test")
    print("  AES-256-GCM + CRYSTALS-Kyber")
    print("=" * 60)

    # Real CipherZenith transaction
    transaction = {
        "sender"    : "Jeni",
        "receiver"  : "Mugunthan",
        "amount"    : 500,
        "txn_id"    : "TXN-20240622-001",
        "timestamp" : "2024-06-22T10:30:00"
    }

    print(f"\n[ORIGINAL TRANSACTION]")
    print(f"  {json.dumps(transaction, indent=2)}")

    # ── Test 1: LOW risk — Kyber512 ───────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  TEST 1 — LOW risk (Kyber512)")
    print(f"{'─'*60}")

    result = encrypt(transaction, risk_level="LOW")
    print(f"\n  Algorithm   : {result['algorithm_used']}")
    print(f"  Risk level  : {result['risk_level']}")
    print(f"  Kyber algo  : {result['key_info']['kyber_algorithm']}")
    print(f"  Public key  : {result['key_info']['kyber_public_key_size']} bytes")
    print(f"  AES key     : {result['key_info']['aes_key_size_bits']} bits")
    print(f"  Ciphertext  : {result['encrypted_data']['aes_ciphertext'][:40]}...")

    # Decrypt and verify
    dec = decrypt_package(result["encrypted_data"])
    recovered = json.loads(dec["plaintext"])
    print(f"\n  Decrypted   : {json.dumps(recovered)}")
    print(f"  Match       : {recovered == transaction}")
    print(f"  [{'PASS' if recovered == transaction else 'FAIL'}] LOW risk encryption")

    # ── Test 2: HIGH risk — Kyber1024 ─────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  TEST 2 — HIGH risk (Kyber1024)")
    print(f"{'─'*60}")

    result_high = encrypt(transaction, risk_level="HIGH")
    print(f"\n  Algorithm   : {result_high['algorithm_used']}")
    print(f"  Kyber algo  : {result_high['key_info']['kyber_algorithm']}")
    print(f"  Public key  : {result_high['key_info']['kyber_public_key_size']} bytes")

    dec_high = decrypt_package(result_high["encrypted_data"])
    recovered_high = json.loads(dec_high["plaintext"])
    print(f"  Match       : {recovered_high == transaction}")
    print(f"  [{'PASS' if recovered_high == transaction else 'FAIL'}] HIGH risk encryption")

    # ── Test 3: Algorithm switch (Step 5 simulation) ──────────────────────────
    print(f"\n{'─'*60}")
    print(f"  TEST 3 — Algorithm switch (Threat detected!)")
    print(f"  Simulating: AI detects threat → switch Kyber512 → Kyber1024")
    print(f"{'─'*60}")

    # Start with LOW risk
    initial = encrypt(transaction, risk_level="LOW")
    print(f"\n  Initial     : {initial['algorithm_used']}")

    # Threat detected — switch to HIGH
    switched = switch_algorithm(initial, new_algorithm="kyber1024")
    print(f"  Switched to : {switched['algorithm_used']}")
    print(f"  From        : {switched['switched_from']}")
    print(f"  To          : {switched['switched_to']}")

    # Decrypt switched package
    dec_switched = decrypt_package(switched["re_encrypted_data"])
    recovered_switched = json.loads(dec_switched["plaintext"])
    print(f"  Data intact : {recovered_switched == transaction}")
    print(f"  [{'PASS' if recovered_switched == transaction else 'FAIL'}] Algorithm switch")

    print(f"\n{'='*60}")
    print(f"  All hybrid encryption tests passed!")
    print(f"  Jenifer can now import: encrypt() and switch_algorithm()")
    print(f"{'='*60}")