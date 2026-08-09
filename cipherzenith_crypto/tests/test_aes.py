"""
test_aes.py — Unit Tests for AES-256-GCM Module
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

Run: python -m pytest tests/test_aes.py -v
 or: python tests/test_aes.py
"""
import os
import sys
import json
import base64

PROJECT_CRYPTO = os.path.join(
    os.path.dirname(__file__),
    "..",
    "cryptography"
)

sys.path.insert(0, PROJECT_CRYPTO)

from cipherzenith_crypto.classical.aes import (
    encrypt,
    decrypt,
    generate_key,
    derive_key_from_secret,
)

# ── Test runner (no pytest needed) ────────────────────────────────────────────

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name} {detail}")
        failed += 1


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_key_generation():
    print("\n── Key Generation ───────────────────────────────────────")

    k = generate_key()
    test("Key is 32 bytes",           len(k) == 32)
    test("Key is bytes type",         isinstance(k, bytes))

    k1, k2 = generate_key(), generate_key()
    test("Every key is unique",       k1 != k2)

    k3, k4 = generate_key(), generate_key()
    test("Uniqueness is consistent",  k3 != k4 and k3 != k1)


def test_basic_encrypt_decrypt():
    print("\n── Basic Encrypt / Decrypt ──────────────────────────────")

    msg = "Hello CipherZenith"
    enc = encrypt(msg)

    test("encrypt() returns dict",           isinstance(enc, dict))
    test("ciphertext key exists",            "ciphertext" in enc)
    test("nonce key exists",                 "nonce" in enc)
    test("key_b64 key exists",              "key_b64" in enc)
    test("mode is AES-256-GCM",             enc["mode"] == "AES-256-GCM")
    test("key_size is 256",                  enc["key_size"] == 256)
    test("ciphertext differs from input",    enc["ciphertext"] != msg)

    dec = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])
    test("decrypt() returns dict",           isinstance(dec, dict))
    test("success is True",                  dec["success"] == True)
    test("plaintext matches original",       dec["plaintext"] == msg)
    test("tampered is False",                dec["tampered"] == False)


def test_transaction_encryption():
    print("\n── Transaction Encryption ───────────────────────────────")

    txn = {
        "sender"    : "Jeni",
        "receiver"  : "Mugunthan",
        "amount"    : 500,
        "txn_id"    : "TXN-20240622-001",
        "timestamp" : "2024-06-22T10:30:00"
    }
    plaintext = json.dumps(txn)
    enc = encrypt(plaintext)
    dec = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])

    recovered = json.loads(dec["plaintext"])
    test("Transaction sender matches",    recovered["sender"] == "Jeni")
    test("Transaction receiver matches",  recovered["receiver"] == "Mugunthan")
    test("Transaction amount matches",    recovered["amount"] == 500)
    test("Transaction txn_id matches",    recovered["txn_id"] == "TXN-20240622-001")
    test("Full transaction dict matches", recovered == txn)


def test_tamper_detection():
    print("\n── Tamper Detection (GCM Authentication) ────────────────")

    enc = encrypt("Sensitive financial data")

    # Modify ciphertext
    bad_ct = enc["ciphertext"][:-4] + "XXXX"
    r1 = decrypt(bad_ct, enc["nonce"], enc["key_b64"])
    test("Modified ciphertext → tampered=True",   r1["tampered"] == True)
    test("Modified ciphertext → success=False",   r1["success"] == False)
    test("Modified ciphertext → plaintext=None",  r1["plaintext"] is None)

    # Wrong key
    wrong_key = base64.b64encode(generate_key()).decode()
    r2 = decrypt(enc["ciphertext"], enc["nonce"], wrong_key)
    test("Wrong key → tampered=True",             r2["tampered"] == True)
    test("Wrong key → success=False",             r2["success"] == False)

    # Wrong nonce
    import os
    wrong_nonce = base64.b64encode(os.urandom(12)).decode()
    r3 = decrypt(enc["ciphertext"], wrong_nonce, enc["key_b64"])
    test("Wrong nonce → tampered=True",           r3["tampered"] == True)

    # Correct data still works after tamper tests
    r4 = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])
    test("Correct data still decrypts after tamper tests", r4["success"] == True)


def test_custom_key():
    print("\n── Custom Key (from Kyber shared secret) ────────────────")

    # Simulate Kyber providing a shared secret
    import os
    kyber_secret = os.urandom(32)
    aes_key      = derive_key_from_secret(kyber_secret)

    test("Derived key is 32 bytes",    len(aes_key) == 32)
    test("Derived key is bytes",       isinstance(aes_key, bytes))

    # Same secret always gives same key (deterministic)
    aes_key2 = derive_key_from_secret(kyber_secret)
    test("Key derivation is deterministic", aes_key == aes_key2)

    # Different secrets give different keys
    other_secret = os.urandom(32)
    aes_key3     = derive_key_from_secret(other_secret)
    test("Different secrets → different keys", aes_key != aes_key3)

    # Encrypt and decrypt using derived key
    msg = "Transaction secured with Kyber-derived key"
    enc = encrypt(msg, aes_key)
    dec = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])
    test("Encrypt/decrypt with derived key", dec["plaintext"] == msg)


def test_edge_cases():
    print("\n── Edge Cases ───────────────────────────────────────────")

    # Empty string
    enc = encrypt("")
    dec = decrypt(enc["ciphertext"], enc["nonce"], enc["key_b64"])
    test("Empty string encrypts and decrypts", dec["plaintext"] == "")

    # Very long message
    long_msg  = "A" * 10000
    long_enc  = encrypt(long_msg)
    long_dec  = decrypt(long_enc["ciphertext"], long_enc["nonce"], long_enc["key_b64"])
    test("10000 char message decrypts correctly", long_dec["plaintext"] == long_msg)

    # Unicode / special characters
    unicode_msg = "Transaction: ₹500 → Mugunthan 🔐"
    enc3 = encrypt(unicode_msg)
    dec3 = decrypt(enc3["ciphertext"], enc3["nonce"], enc3["key_b64"])
    test("Unicode message (₹, emoji) works",  dec3["plaintext"] == unicode_msg)

    # Each encryption produces different ciphertext (nonce is random)
    msg = "same message"
    e1  = encrypt(msg)
    e2  = encrypt(msg)
    test("Same plaintext → different ciphertext each time", e1["ciphertext"] != e2["ciphertext"])
    test("Same plaintext → different nonce each time",      e1["nonce"] != e2["nonce"])

    # But both decrypt to same value
    d1 = decrypt(e1["ciphertext"], e1["nonce"], e1["key_b64"])
    d2 = decrypt(e2["ciphertext"], e2["nonce"], e2["key_b64"])
    test("Both ciphertexts decrypt to same plaintext",
         d1["plaintext"] == d2["plaintext"] == msg)


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("  CipherZenith — AES-256-GCM Unit Tests")
    print("=" * 58)

    test_key_generation()
    test_basic_encrypt_decrypt()
    test_transaction_encryption()
    test_tamper_detection()
    test_custom_key()
    test_edge_cases()

    print(f"\n{'='*58}")
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print(f"  ✅ All tests passed — aes.py is production ready")
    else:
        print(f"  ❌ {failed} test(s) failed — fix before pushing")
    print(f"{'='*58}")