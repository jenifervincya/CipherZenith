"""
hybrid_scheme.py — Hybrid Encryption: AES-256-GCM + CRYSTALS-Kyber
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

Two modes (auto-detected at startup):
  REAL MODE     : liboqs available → genuine Kyber512/1024 PQC
  FALLBACK MODE : liboqs not available → simulated Kyber (same API, same return shape)

Jenifer's backend uses the same import either way:
  from cryptography.hybrid.hybrid_scheme import encrypt, switch_algorithm

Function signatures and return shapes are IDENTICAL in both modes.
"""

import os
import sys
import json
import base64
import hashlib
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classical.aes import encrypt as aes_encrypt, decrypt as aes_decrypt, derive_key_from_secret


# ── Detect liboqs availability ─────────────────────────────────────────────────

try:
    import oqs
    # Quick test to confirm it actually works
    with oqs.KeyEncapsulation("Kyber512") as _k:
        _k.generate_keypair()
    LIBOQS_AVAILABLE = True
    print("[HYBRID] Mode: REAL — liboqs available, using genuine Kyber PQC")
except BaseException:
    LIBOQS_AVAILABLE = False
    print("[HYBRID] Mode: FALLBACK — liboqs not available, using simulated Kyber")
    print("[HYBRID] Return shapes identical — Jenifer's backend unaffected")


# ── Key sizes (same values real Kyber produces) ────────────────────────────────

KYBER_PARAMS = {
    "Kyber512"  : {"public_key_size": 800,  "private_key_size": 1632, "ct_size": 768,  "ss_size": 32},
    "Kyber1024" : {"public_key_size": 1568, "private_key_size": 3168, "ct_size": 1568, "ss_size": 32},
}

RISK_ALGORITHM = {
    "LOW"    : "kyber512",
    "MEDIUM" : "kyber512",
    "HIGH"   : "kyber1024",
}

_session_keys = {}


# ── Real Kyber (liboqs) ────────────────────────────────────────────────────────

def _real_generate_keypair(algorithm: str) -> dict:
    algo_name = "Kyber512" if "512" in algorithm else "Kyber1024"
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

def _real_encapsulate(public_key_b64: str, algorithm: str) -> dict:
    algo_name  = "Kyber512" if "512" in algorithm else "Kyber1024"
    public_key = base64.b64decode(public_key_b64)
    with oqs.KeyEncapsulation(algo_name) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)
    return {
        "ciphertext"         : base64.b64encode(ciphertext).decode(),
        "shared_secret"      : base64.b64encode(shared_secret).decode(),
        "algorithm"          : algo_name,
        "ciphertext_size"    : len(ciphertext),
        "shared_secret_size" : len(shared_secret),
    }

def _real_decapsulate(ciphertext_b64: str, private_key_b64: str, algorithm: str) -> dict:
    algo_name   = "Kyber512" if "512" in algorithm else "Kyber1024"
    ciphertext  = base64.b64decode(ciphertext_b64)
    private_key = base64.b64decode(private_key_b64)
    with oqs.KeyEncapsulation(algo_name, secret_key=private_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)
    return {
        "shared_secret"      : base64.b64encode(shared_secret).decode(),
        "algorithm"          : algo_name,
        "shared_secret_size" : len(shared_secret),
    }


# ── Fallback Kyber (simulated — same return shape) ────────────────────────────

def _fallback_generate_keypair(algorithm: str) -> dict:
    """
    Simulates Kyber keypair generation.
    Uses cryptographically secure random bytes.
    Return shape is IDENTICAL to real Kyber output.
    """
    algo_name = "Kyber512" if "512" in algorithm else "Kyber1024"
    params    = KYBER_PARAMS[algo_name]

    # Generate secure random bytes matching real Kyber key sizes
    public_key  = secrets.token_bytes(params["public_key_size"])
    private_key = secrets.token_bytes(params["private_key_size"])

    # Store private key for later decapsulation (keyed by public key hash)
    _pk_hash = hashlib.sha256(public_key).hexdigest()
    _fallback_store[_pk_hash] = private_key

    return {
        "public_key"       : base64.b64encode(public_key).decode(),
        "private_key"      : base64.b64encode(private_key).decode(),
        "algorithm"        : algo_name,
        "public_key_size"  : len(public_key),
        "private_key_size" : len(private_key),
    }

_fallback_store = {}   # stores shared secrets keyed by ciphertext hash

def _fallback_encapsulate(public_key_b64: str, algorithm: str) -> dict:
    """
    Simulates Kyber encapsulation.
    Generates a secure random shared secret and ciphertext.
    Return shape IDENTICAL to real Kyber output.
    """
    algo_name     = "Kyber512" if "512" in algorithm else "Kyber1024"
    params        = KYBER_PARAMS[algo_name]
    public_key    = base64.b64decode(public_key_b64)

    # Shared secret: 32 secure random bytes (matches real Kyber output)
    shared_secret = secrets.token_bytes(32)

    # Ciphertext: derived from public key + shared secret (deterministic)
    # So decapsulation can recover it
    ct_material = hashlib.sha256(public_key + shared_secret).digest()
    ciphertext  = ct_material * (params["ct_size"] // 32) + \
                  ct_material[:params["ct_size"] % 32]

    # Store shared secret keyed by ciphertext so decap can retrieve it
    ct_hash = hashlib.sha256(ciphertext).hexdigest()
    _fallback_store[ct_hash] = shared_secret

    return {
        "ciphertext"         : base64.b64encode(ciphertext).decode(),
        "shared_secret"      : base64.b64encode(shared_secret).decode(),
        "algorithm"          : algo_name,
        "ciphertext_size"    : len(ciphertext),
        "shared_secret_size" : len(shared_secret),
    }

def _fallback_decapsulate(ciphertext_b64: str, private_key_b64: str, algorithm: str) -> dict:
    """
    Simulates Kyber decapsulation.
    Retrieves stored shared secret using ciphertext as key.
    Return shape IDENTICAL to real Kyber output.
    """
    algo_name  = "Kyber512" if "512" in algorithm else "Kyber1024"
    ciphertext = base64.b64decode(ciphertext_b64)
    ct_hash    = hashlib.sha256(ciphertext).hexdigest()

    if ct_hash not in _fallback_store:
        raise ValueError("[FALLBACK] Shared secret not found — session may have been rotated")

    shared_secret = _fallback_store[ct_hash]

    return {
        "shared_secret"      : base64.b64encode(shared_secret).decode(),
        "algorithm"          : algo_name,
        "shared_secret_size" : len(shared_secret),
    }

def _fallback_rotate(algorithm: str) -> dict:
    print(f"[KYBER FALLBACK] Key rotation triggered — generating fresh {algorithm} keypair")
    return _fallback_generate_keypair(algorithm)


# ── Unified interface — picks real or fallback automatically ──────────────────

def _generate_keypair(algorithm: str) -> dict:
    return _real_generate_keypair(algorithm) if LIBOQS_AVAILABLE \
           else _fallback_generate_keypair(algorithm)

def _encapsulate(public_key_b64: str, algorithm: str) -> dict:
    return _real_encapsulate(public_key_b64, algorithm) if LIBOQS_AVAILABLE \
           else _fallback_encapsulate(public_key_b64, algorithm)

def _decapsulate(ciphertext_b64: str, private_key_b64: str, algorithm: str) -> dict:
    return _real_decapsulate(ciphertext_b64, private_key_b64, algorithm) if LIBOQS_AVAILABLE \
           else _fallback_decapsulate(ciphertext_b64, private_key_b64, algorithm)

def _rotate(algorithm: str) -> dict:
    if LIBOQS_AVAILABLE:
        print(f"[KYBER] Key rotation triggered — generating fresh {algorithm} keypair")
        return _real_generate_keypair(algorithm)
    return _fallback_rotate(algorithm)


# ── Session management ─────────────────────────────────────────────────────────

def _get_or_create_keypair(algorithm: str) -> dict:
    if algorithm not in _session_keys:
        print(f"[HYBRID] Generating fresh {algorithm} keypair for session")
        _session_keys[algorithm] = _generate_keypair(algorithm)
    return _session_keys[algorithm]


# ── PUBLIC API — Jenifer imports these two functions ──────────────────────────

def encrypt(transaction_data: dict, risk_level: str = "LOW") -> dict:
    """
    Encrypt transaction data using Hybrid AES-256 + Kyber.
    Called by Jenifer's backend at Step 2.

    Args:
        transaction_data : dict  e.g. {"sender": "Jeni", "receiver": "Mugunthan", "amount": 500}
        risk_level       : "LOW" | "MEDIUM" | "HIGH"

    Returns:
        {
            "encrypted_data" : { aes_ciphertext, aes_nonce, kyber_ciphertext, ... },
            "algorithm_used" : "AES-256-GCM + Kyber512",
            "key_info"       : { kyber_algorithm, public_key_size, aes_key_size_bits, ... },
            "risk_level"     : "LOW"
        }
    """
    algorithm = RISK_ALGORITHM.get(risk_level.upper(), "kyber512")
    keypair   = _get_or_create_keypair(algorithm)
    enc_result = _encapsulate(keypair["public_key"], algorithm)

    shared_secret_bytes = base64.b64decode(enc_result["shared_secret"])
    aes_key             = derive_key_from_secret(shared_secret_bytes)
    plaintext           = json.dumps(transaction_data)
    aes_result          = aes_encrypt(plaintext, aes_key)

    algo_label = f"AES-256-GCM + {'Kyber512' if '512' in algorithm else 'Kyber1024'}"

    encrypted_data = {
        "aes_ciphertext"   : aes_result["ciphertext"],
        "aes_nonce"        : aes_result["nonce"],
        "aes_mode"         : aes_result["mode"],
        "kyber_ciphertext" : enc_result["ciphertext"],
        "kyber_algorithm"  : enc_result["algorithm"],
        "algorithm_label"  : algo_label,
        "risk_level"       : risk_level.upper(),
    }

    key_info = {
        "kyber_algorithm"        : enc_result["algorithm"],
        "kyber_public_key_size"  : keypair["public_key_size"],
        "aes_key_size_bits"      : 256,
        "shared_secret_size"     : enc_result["shared_secret_size"],
        "mode"                   : "REAL" if LIBOQS_AVAILABLE else "FALLBACK",
    }

    return {
        "encrypted_data" : encrypted_data,
        "algorithm_used" : algo_label,
        "key_info"       : key_info,
        "risk_level"     : risk_level.upper(),
    }


def switch_algorithm(encrypted_package: dict, new_algorithm: str = "kyber1024") -> dict:
    """
    Re-encrypt with stronger algorithm when threat detected.
    Called by Jenifer's backend at Step 5.

    Args:
        encrypted_package : full dict returned by encrypt()
        new_algorithm     : "kyber1024" (always on HIGH threat)

    Returns:
        {
            "re_encrypted_data" : { aes_ciphertext, aes_nonce, kyber_ciphertext, ... },
            "algorithm_used"    : "AES-256-GCM + Kyber1024",
            "key_info"          : { ... },
            "switched_from"     : "AES-256-GCM + Kyber512",
            "switched_to"       : "AES-256-GCM + Kyber1024"
        }
    """
    encrypted_data    = encrypted_package.get("encrypted_data", encrypted_package)
    old_algo_label    = encrypted_data.get("algorithm_label", "Unknown")
    old_kyber_algo    = encrypted_data.get("kyber_algorithm", "Kyber512")
    old_algo_key      = "kyber512" if "512" in old_kyber_algo else "kyber1024"

    if old_algo_key not in _session_keys:
        raise ValueError("Original session keys not found — cannot switch algorithm")

    old_keypair = _session_keys[old_algo_key]

    # Recover AES key via Kyber decapsulation
    dec_result          = _decapsulate(encrypted_data["kyber_ciphertext"],
                                       old_keypair["private_key"], old_algo_key)
    shared_secret_bytes = base64.b64decode(dec_result["shared_secret"])
    old_aes_key         = derive_key_from_secret(shared_secret_bytes)

    # Decrypt AES to recover plaintext
    aes_dec = aes_decrypt(
        encrypted_data["aes_ciphertext"],
        encrypted_data["aes_nonce"],
        base64.b64encode(old_aes_key).decode()
    )
    if not aes_dec["success"]:
        raise ValueError(f"Decryption failed during switch: {aes_dec.get('error')}")

    plaintext = aes_dec["plaintext"]

    # Rotate keys and re-encrypt with new algorithm
    new_algo_key  = new_algorithm.lower().replace("-", "")
    print(f"[HYBRID] Switching algorithm: {old_kyber_algo} → {new_algorithm.upper()}")
    print(f"[HYBRID] Rotating keys — all old sessions invalidated")
    _session_keys[new_algo_key] = _rotate(new_algo_key)

    new_keypair   = _session_keys[new_algo_key]
    new_enc       = _encapsulate(new_keypair["public_key"], new_algo_key)
    new_ss_bytes  = base64.b64decode(new_enc["shared_secret"])
    new_aes_key   = derive_key_from_secret(new_ss_bytes)
    new_aes       = aes_encrypt(plaintext, new_aes_key)

    new_algo_label = f"AES-256-GCM + {'Kyber512' if '512' in new_algo_key else 'Kyber1024'}"

    re_encrypted_data = {
        "aes_ciphertext"   : new_aes["ciphertext"],
        "aes_nonce"        : new_aes["nonce"],
        "aes_mode"         : new_aes["mode"],
        "kyber_ciphertext" : new_enc["ciphertext"],
        "kyber_algorithm"  : new_enc["algorithm"],
        "algorithm_label"  : new_algo_label,
        "risk_level"       : "HIGH",
    }

    key_info = {
        "kyber_algorithm"       : new_enc["algorithm"],
        "kyber_public_key_size" : new_keypair["public_key_size"],
        "aes_key_size_bits"     : 256,
        "shared_secret_size"    : new_enc["shared_secret_size"],
        "mode"                  : "REAL" if LIBOQS_AVAILABLE else "FALLBACK",
    }

    return {
        "re_encrypted_data" : re_encrypted_data,
        "algorithm_used"    : new_algo_label,
        "key_info"          : key_info,
        "switched_from"     : old_algo_label,
        "switched_to"       : new_algo_label,
    }


def decrypt_package(encrypted_data: dict) -> dict:
    """Helper for testing and verification."""
    kyber_algo = encrypted_data.get("kyber_algorithm", "Kyber512")
    algo_key   = "kyber512" if "512" in kyber_algo else "kyber1024"

    if algo_key not in _session_keys:
        raise ValueError("Session keys not found — cannot decrypt")

    keypair = _session_keys[algo_key]
    dec     = _decapsulate(encrypted_data["kyber_ciphertext"],
                           keypair["private_key"], algo_key)

    ss_bytes = base64.b64decode(dec["shared_secret"])
    aes_key  = derive_key_from_secret(ss_bytes)

    return aes_decrypt(
        encrypted_data["aes_ciphertext"],
        encrypted_data["aes_nonce"],
        base64.b64encode(aes_key).decode()
    )


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  CipherZenith — Hybrid Encryption Module")
    print(f"  Mode: {'REAL (liboqs)' if LIBOQS_AVAILABLE else 'FALLBACK (simulated)'}")
    print("=" * 60)

    txn = {"sender": "Jeni", "receiver": "Mugunthan",
           "amount": 500, "txn_id": "TXN-DEMO-001"}

    print(f"\n[1] Encrypting at LOW risk...")
    r = encrypt(txn, "LOW")
    print(f"    Algorithm : {r['algorithm_used']}")
    dec = decrypt_package(r["encrypted_data"])
    print(f"    Decrypted : {dec['plaintext']}")
    print(f"    Match     : {json.loads(dec['plaintext']) == txn}")

    print(f"\n[2] Switching to HIGH (threat detected)...")
    s = switch_algorithm(r, "kyber1024")
    print(f"    From      : {s['switched_from']}")
    print(f"    To        : {s['switched_to']}")
    dec2 = decrypt_package(s["re_encrypted_data"])
    print(f"    Intact    : {json.loads(dec2['plaintext']) == txn}")

    print(f"\n✅ Both modes use identical API — Jenifer's code unchanged")