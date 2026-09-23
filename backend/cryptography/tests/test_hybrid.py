"""
test_hybrid.py — Unit Tests for Hybrid Encryption Module
CipherZenith | ByteStorm Crew | Tamilvel Mugunthan S

Tests the two functions Jenifer's backend calls:
  - encrypt(transaction_data, risk_level)
  - switch_algorithm(encrypted_package, new_algorithm)

Run: python tests/test_hybrid.py
     (from inside cryptography/ folder)
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hybrid.hybrid_scheme import encrypt, switch_algorithm, decrypt_package

# ── Test runner ────────────────────────────────────────────────────────────────

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

# ── Sample transactions ────────────────────────────────────────────────────────

TXN_NORMAL = {
    "sender"    : "Jeni",
    "receiver"  : "Mugunthan",
    "amount"    : 500,
    "txn_id"    : "TXN-20240622-001",
    "timestamp" : "2024-06-22T10:30:00"
}

TXN_HIGH_VALUE = {
    "sender"    : "Trishna",
    "receiver"  : "Mohamed",
    "amount"    : 999999,
    "txn_id"    : "TXN-20240622-002",
    "timestamp" : "2024-06-22T11:00:00"
}


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_encrypt_return_structure():
    print("\n── encrypt() Return Structure ───────────────────────────")

    result = encrypt(TXN_NORMAL, risk_level="LOW")

    test("Returns dict",                     isinstance(result, dict))
    test("encrypted_data key exists",        "encrypted_data" in result)
    test("algorithm_used key exists",        "algorithm_used" in result)
    test("key_info key exists",              "key_info" in result)
    test("risk_level key exists",            "risk_level" in result)

    ed = result["encrypted_data"]
    test("aes_ciphertext in encrypted_data", "aes_ciphertext" in ed)
    test("aes_nonce in encrypted_data",      "aes_nonce" in ed)
    test("kyber_ciphertext in encrypted_data","kyber_ciphertext" in ed)
    test("kyber_algorithm in encrypted_data","kyber_algorithm" in ed)
    test("algorithm_label in encrypted_data","algorithm_label" in ed)

    ki = result["key_info"]
    test("key_info has kyber_algorithm",     "kyber_algorithm" in ki)
    test("key_info has aes_key_size_bits",   "aes_key_size_bits" in ki)
    test("AES key is always 256 bits",       ki["aes_key_size_bits"] == 256)


def test_low_risk_encryption():
    print("\n── LOW Risk — AES-256-GCM + Kyber512 ───────────────────")

    result = encrypt(TXN_NORMAL, risk_level="LOW")

    test("risk_level echoed as LOW",         result["risk_level"] == "LOW")
    test("algorithm_used contains Kyber512", "Kyber512" in result["algorithm_used"])
    test("algorithm_used contains AES-256",  "AES-256" in result["algorithm_used"])
    test("Kyber algo is Kyber512",           result["key_info"]["kyber_algorithm"] == "Kyber512")
    test("Public key is 800 bytes",          result["key_info"]["kyber_public_key_size"] == 800)

    # Decrypt and verify
    dec = decrypt_package(result["encrypted_data"])
    recovered = json.loads(dec["plaintext"])
    test("Decryption succeeds",              dec["success"] == True)
    test("Full transaction recovered",       recovered == TXN_NORMAL)
    test("Sender matches",                   recovered["sender"] == "Jeni")
    test("Amount matches",                   recovered["amount"] == 500)


def test_medium_risk_encryption():
    print("\n── MEDIUM Risk — AES-256-GCM + Kyber512 ────────────────")

    result = encrypt(TXN_NORMAL, risk_level="MEDIUM")

    test("risk_level echoed as MEDIUM",      result["risk_level"] == "MEDIUM")
    test("Uses Kyber512 at MEDIUM risk",     "Kyber512" in result["algorithm_used"])

    dec = decrypt_package(result["encrypted_data"])
    recovered = json.loads(dec["plaintext"])
    test("Transaction recovered at MEDIUM",  recovered == TXN_NORMAL)


def test_high_risk_encryption():
    print("\n── HIGH Risk — AES-256-GCM + Kyber1024 ─────────────────")

    result = encrypt(TXN_NORMAL, risk_level="HIGH")

    test("risk_level echoed as HIGH",        result["risk_level"] == "HIGH")
    test("algorithm_used contains Kyber1024","Kyber1024" in result["algorithm_used"])
    test("Kyber algo is Kyber1024",          result["key_info"]["kyber_algorithm"] == "Kyber1024")
    test("Public key is 1568 bytes",         result["key_info"]["kyber_public_key_size"] == 1568)

    dec = decrypt_package(result["encrypted_data"])
    recovered = json.loads(dec["plaintext"])
    test("Decryption succeeds at HIGH risk", dec["success"] == True)
    test("Full transaction recovered",       recovered == TXN_NORMAL)


def test_all_risk_levels_same_data():
    print("\n── All Risk Levels Recover Same Data ────────────────────")

    for level in ["LOW", "MEDIUM", "HIGH"]:
        result = encrypt(TXN_HIGH_VALUE, risk_level=level)
        dec    = decrypt_package(result["encrypted_data"])
        recovered = json.loads(dec["plaintext"])
        test(f"{level} risk recovers correct transaction",
             recovered == TXN_HIGH_VALUE)
        test(f"{level} risk amount is correct",
             recovered["amount"] == 999999)


def test_switch_algorithm():
    print("\n── switch_algorithm() — Threat Detected Simulation ─────")

    # Start with LOW risk
    initial = encrypt(TXN_NORMAL, risk_level="LOW")
    test("Initial algorithm is Kyber512",
         "Kyber512" in initial["algorithm_used"])

    # Threat detected — switch to Kyber1024
    switched = switch_algorithm(initial, new_algorithm="kyber1024")

    test("switched_from exists",             "switched_from" in switched)
    test("switched_to exists",               "switched_to" in switched)
    test("re_encrypted_data exists",         "re_encrypted_data" in switched)
    test("algorithm_used exists",            "algorithm_used" in switched)
    test("Switched to contains Kyber1024",   "Kyber1024" in switched["algorithm_used"])
    test("switched_from was Kyber512",       "Kyber512" in switched["switched_from"])
    test("switched_to is Kyber1024",         "Kyber1024" in switched["switched_to"])

    # Verify data survived the switch
    dec = decrypt_package(switched["re_encrypted_data"])
    recovered = json.loads(dec["plaintext"])
    test("Data intact after switch",         recovered == TXN_NORMAL)
    test("Sender intact after switch",       recovered["sender"] == "Jeni")
    test("Amount intact after switch",       recovered["amount"] == 500)
    test("txn_id intact after switch",       recovered["txn_id"] == "TXN-20240622-001")


def test_switch_preserves_all_fields():
    print("\n── switch_algorithm() Preserves All Fields ──────────────")

    complex_txn = {
        "sender"    : "Trishna",
        "receiver"  : "Jeni",
        "amount"    : 12345,
        "txn_id"    : "TXN-COMPLEX-999",
        "timestamp" : "2024-06-22T23:59:59",
        "note"      : "Test with special chars: ₹ & <> !@#"
    }

    initial  = encrypt(complex_txn, risk_level="LOW")
    switched = switch_algorithm(initial, new_algorithm="kyber1024")
    dec      = decrypt_package(switched["re_encrypted_data"])
    recovered = json.loads(dec["plaintext"])

    test("All fields preserved after switch", recovered == complex_txn)
    test("Special chars preserved",
         recovered["note"] == "Test with special chars: ₹ & <> !@#")


def test_ciphertext_is_different_each_time():
    print("\n── Ciphertext Uniqueness (Nonce randomness) ─────────────")

    r1 = encrypt(TXN_NORMAL, risk_level="LOW")
    r2 = encrypt(TXN_NORMAL, risk_level="LOW")

    test("Same input → different ciphertext each time",
         r1["encrypted_data"]["aes_ciphertext"] !=
         r2["encrypted_data"]["aes_ciphertext"])

    test("Same input → different nonce each time",
         r1["encrypted_data"]["aes_nonce"] !=
         r2["encrypted_data"]["aes_nonce"])

    # But both decrypt correctly
    d1 = decrypt_package(r1["encrypted_data"])
    d2 = decrypt_package(r2["encrypted_data"])
    test("Both ciphertexts decrypt to same transaction",
         json.loads(d1["plaintext"]) == json.loads(d2["plaintext"]))


def test_jenifer_integration_simulation():
    print("\n── Jenifer Backend Integration Simulation ───────────────")
    print("   Simulating the full 8-step CipherZenith pipeline...\n")

    # Step 1 — transaction arrives
    transaction = {
        "sender"    : "Jeni",
        "receiver"  : "Mugunthan",
        "amount"    : 500,
        "txn_id"    : "TXN-DEMO-001"
    }
    print(f"   Step 1 — Transaction: {transaction['sender']} → "
          f"{transaction['receiver']} ₹{transaction['amount']}")

    # Step 2 — Jenifer calls encrypt() at LOW risk
    encrypted = encrypt(transaction, risk_level="LOW")
    print(f"   Step 2 — Encrypted: {encrypted['algorithm_used']}")
    test("Step 2 encryption succeeds",
         "aes_ciphertext" in encrypted["encrypted_data"])

    # Step 3 & 4 — AI detects threat (simulated)
    threat_detected = True
    print(f"   Step 3 — AI anomaly score: 0.87 (HIGH)")
    print(f"   Step 4 — Threat detected: Replay Attack (confidence 87%)")

    # Step 5 — Jenifer calls switch_algorithm()
    if threat_detected:
        switched = switch_algorithm(encrypted, new_algorithm="kyber1024")
        print(f"   Step 5 — Switched: {switched['switched_from']} → "
              f"{switched['switched_to']}")
        test("Step 5 algorithm switch succeeds",
             "Kyber1024" in switched["algorithm_used"])
        final_package = switched["re_encrypted_data"]
    else:
        final_package = encrypted["encrypted_data"]

    # Step 6–8 — self-healing, transmission, output
    dec       = decrypt_package(final_package)
    recovered = json.loads(dec["plaintext"])
    print(f"   Step 8 — Transaction delivered: {dec['success']}")

    test("Full pipeline: data intact end-to-end", recovered == transaction)
    test("Full pipeline: amount correct",         recovered["amount"] == 500)
    test("Full pipeline: no tampering",           dec["tampered"] == False)

    print(f"\n   ✅ Full 8-step pipeline simulation complete")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 58)
    print("  CipherZenith — Hybrid Encryption Unit Tests")
    print("  AES-256-GCM + CRYSTALS-Kyber")
    print("=" * 58)

    test_encrypt_return_structure()
    test_low_risk_encryption()
    test_medium_risk_encryption()
    test_high_risk_encryption()
    test_all_risk_levels_same_data()
    test_switch_algorithm()
    test_switch_preserves_all_fields()
    test_ciphertext_is_different_each_time()
    test_jenifer_integration_simulation()

    print(f"\n{'='*58}")
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print(f"  ✅ All tests passed — hybrid_scheme.py is production ready")
        print(f"  ✅ Jenifer can safely import encrypt() and switch_algorithm()")
    else:
        print(f"  ❌ {failed} test(s) failed — fix before handing off to Jenifer")
    print(f"{'='*58}")