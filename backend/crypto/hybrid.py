"""
hybrid.py - Step 2 encryption adapter

Keeps the interface main.py already uses:
  encrypt(transaction_data, risk_level)       -> {encrypted_data, algorithm_used, key_info}
  switch_algorithm(encrypted_data, new_algo)  -> {re_encrypted_data, algorithm_used, key_info}

Default: the original simulated stub, so nothing changes on a server without liboqs.
Opt in to the real AES-256-GCM + Kyber module (cryptography/hybrid/hybrid_scheme.py):
  CIPHERZENITH_REAL_HYBRID=1 python -m uvicorn main:app --reload

The dashboard expects short strings, so the adapter returns a fingerprint of the real
ciphertext and keeps the full encrypted package in memory for switch_algorithm.
"""
import hashlib
import importlib
import json
import os
import sys
import uuid
from collections import OrderedDict

# <repo>/cryptography, found relative to this file (<repo>/backend/crypto/hybrid.py)
_CRYPTO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cryptography",
)
_MAX_PACKAGES = 200

_real = None                 # the loaded hybrid_scheme module, once loaded
_real_failed = False         # True after a failed load, so we do not retry on every request
_packages = OrderedDict()    # preview string -> real encrypted package


def _use_real():
    return os.environ.get("CIPHERZENITH_REAL_HYBRID") == "1"


def _load_real():
    global _real, _real_failed
    if _real is not None:
        return _real
    if _real_failed:
        return None
    try:
        if sys.path[0] != _CRYPTO_DIR:
            sys.path.insert(0, _CRYPTO_DIR)
        _real = importlib.import_module("hybrid.hybrid_scheme")
    except (Exception, SystemExit) as e:   # SystemExit: a failed liboqs build can exit
        _real_failed = True
        print(f"[CRYPTO] Real hybrid module unavailable ({type(e).__name__}); using simulated stub")
        return None
    return _real


def _fingerprint(encrypted_data):
    return hashlib.sha256(encrypted_data["aes_ciphertext"].encode()).hexdigest()[:12]


def _label(kyber_algorithm):
    # Same wording the adaptive engine uses in Steps 5 and 8, so the dashboard stays consistent.
    return f"AES-256 + {kyber_algorithm}"


def _key_info(info):
    mode = "real Kyber" if info["mode"] == "REAL" else "simulated Kyber (liboqs unavailable)"
    return f"{info['kyber_algorithm']} session key, {mode}"


def _remember(preview, package):
    _packages[preview] = package
    while len(_packages) > _MAX_PACKAGES:
        _packages.popitem(last=False)


def _stub_encrypt():
    return {
        "encrypted_data": f"[encrypted-{uuid.uuid4().hex[:12]}]",
        "algorithm_used": "AES-256 + Kyber512",
        "key_info": "session-key-simulated",
    }


def _stub_switch(new_algorithm):
    return {
        "re_encrypted_data": f"[re-encrypted-{uuid.uuid4().hex[:12]}]",
        "algorithm_used": new_algorithm,
        "key_info": "session-key-rotated",
    }


def encrypt(transaction_data: dict, risk_level: str) -> dict:
    real = _load_real() if _use_real() else None
    if real is None:
        return _stub_encrypt()
    try:
        # The signature was verified before this step; encrypting it adds nothing.
        payload = {k: v for k, v in transaction_data.items() if k != "signature"}
        result = real.encrypt(payload, risk_level=risk_level)
        preview = f"[encrypted-{_fingerprint(result['encrypted_data'])}]"
    except Exception as e:
        print(f"[CRYPTO] Real encrypt failed ({type(e).__name__}: {e}); using simulated stub")
        return _stub_encrypt()
    _remember(preview, {"encrypted_data": result["encrypted_data"]})
    return {
        "encrypted_data": preview,
        "algorithm_used": _label(result["key_info"]["kyber_algorithm"]),
        "key_info": _key_info(result["key_info"]),
    }


def switch_algorithm(encrypted_data: str, new_algorithm: str) -> dict:
    real = _load_real() if _use_real() else None
    package = _packages.get(encrypted_data) if real is not None else None
    if package is None:
        return _stub_switch(new_algorithm)
    target = "kyber1024" if "1024" in new_algorithm else "kyber512"
    try:
        result = real.switch_algorithm(package, new_algorithm=target)
        preview = f"[re-encrypted-{_fingerprint(result['re_encrypted_data'])}]"
    except Exception as e:
        print(f"[CRYPTO] Real switch failed ({type(e).__name__}: {e}); using simulated stub")
        return _stub_switch(new_algorithm)
    _remember(preview, {"encrypted_data": result["re_encrypted_data"]})
    return {
        "re_encrypted_data": preview,
        "algorithm_used": _label(result["key_info"]["kyber_algorithm"]),
        "key_info": _key_info(result["key_info"]) + ", keys rotated",
    }


def _debug_decrypt(preview):
    """Self-test helper: decrypt a stored package with the real module. Not used by the pipeline."""
    return _real.decrypt_package(_packages[preview]["encrypted_data"])


# -- Self-test: run `python backend/crypto/hybrid.py` from the repo root -------------
if __name__ == "__main__":
    print("=" * 62)
    print("  CipherZenith - Step 2 adapter self-test")
    print("=" * 62)

    failures = 0

    def check(name, ok):
        global failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures += 1

    txn = {"sender": "Jeni", "receiver": "Mugunthan", "amount": 500.0,
           "nonce": "n-1", "timestamp": 1.0, "signature": "SIG" * 100}
    expected_payload = {k: v for k, v in txn.items() if k != "signature"}
    SHAPE = {"encrypted_data", "algorithm_used", "key_info"}

    os.environ.pop("CIPHERZENITH_REAL_HYBRID", None)
    r = encrypt(txn, "LOW")
    check("flag off: stub shape and simulated key_info",
          set(r) == SHAPE and r["key_info"] == "session-key-simulated")

    os.environ["CIPHERZENITH_REAL_HYBRID"] = "1"
    r1 = encrypt(txn, "LOW")
    r2 = encrypt(txn, "LOW")
    check("flag on: same three keys as the stub, all strings",
          set(r1) == SHAPE and all(isinstance(v, str) for v in r1.values()))
    check("LOW risk -> AES-256 + Kyber512", r1["algorithm_used"] == "AES-256 + Kyber512")
    check("key_info names the Kyber session key", r1["key_info"].startswith("Kyber512 session key"))
    check("preview looks like the stub's",
          r1["encrypted_data"].startswith("[encrypted-") and r1["encrypted_data"].endswith("]"))
    check("same transaction twice -> different ciphertext", r1["encrypted_data"] != r2["encrypted_data"])
    recovered = json.loads(_debug_decrypt(r1["encrypted_data"])["plaintext"])
    check("real ciphertext decrypts to the transaction (signature not encrypted)",
          recovered == expected_payload)
    check("HIGH risk -> AES-256 + Kyber1024", encrypt(txn, "HIGH")["algorithm_used"] == "AES-256 + Kyber1024")

    s = switch_algorithm(r1["encrypted_data"], "Kyber1024")
    check("switch: same three-key shape as the stub",
          set(s) == {"re_encrypted_data", "algorithm_used", "key_info"})
    check("switch: preview looks like the stub's", s["re_encrypted_data"].startswith("[re-encrypted-"))
    check("switch: algorithm is AES-256 + Kyber1024", s["algorithm_used"] == "AES-256 + Kyber1024")
    recovered2 = json.loads(_debug_decrypt(s["re_encrypted_data"])["plaintext"])
    check("data intact after the switch", recovered2 == expected_payload)
    check("unknown ciphertext id falls back without crashing",
          "re_encrypted_data" in switch_algorithm("[encrypted-doesnotexist]", "Kyber1024"))

    saved_real, saved_failed, saved_import = _real, _real_failed, importlib.import_module
    _real, _real_failed = None, False
    importlib.import_module = lambda name: (_ for _ in ()).throw(ImportError("simulated"))
    r3 = encrypt(txn, "LOW")
    importlib.import_module = saved_import
    _real, _real_failed = saved_real, saved_failed
    check("real module unavailable -> falls back to the stub", r3["key_info"] == "session-key-simulated")

    print("\n" + "=" * 62)
    print("  All checks passed" if failures == 0 else f"  {failures} check(s) FAILED")
    print("=" * 62)
