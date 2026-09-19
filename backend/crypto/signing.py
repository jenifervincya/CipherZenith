import base64
import json
import os

TRUSTED_KEYS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trusted_keys.json"
)

# Flip to True once every client signs its transactions.
REQUIRE_SIGNATURE = False


def canonical_message(sender, receiver, amount, nonce, timestamp) -> str:
    """The exact string that gets signed. Client and server must build it identically."""
    return json.dumps(
        {
            "sender": sender,
            "receiver": receiver,
            "amount": float(amount),
            "nonce": nonce,
            "timestamp": float(timestamp),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _load_trusted_keys() -> dict:
    # Read per request so a new key doesn't need a server restart.
    try:
        with open(TRUSTED_KEYS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def verify_signature(sender, receiver, amount, nonce, timestamp, signature_b64) -> dict:
    """
    Returns {"status": ..., "reason": ...} where status is one of:
      verified   - signature is valid for this exact transaction
      unchecked  - no signature supplied (legacy client, allowed while REQUIRE_SIGNATURE is False)
      invalid    - missing/unknown key, bad signature, or verifier unavailable
    """
    if signature_b64 is None:
        if REQUIRE_SIGNATURE:
            return {"status": "invalid", "reason": "Signature is required"}
        return {"status": "unchecked", "reason": "No signature supplied (legacy client)"}

    if nonce is None or timestamp is None:
        return {"status": "invalid", "reason": "A signed transaction needs nonce and timestamp"}

    entry = _load_trusted_keys().get(sender)
    if entry is None:
        return {"status": "invalid", "reason": f"No trusted public key for sender '{sender}'"}

    # Imported here so the backend still starts on machines without liboqs.
    try:
        import oqs
    except (Exception, SystemExit):
        return {"status": "invalid", "reason": "Signature verification unavailable on this server"}

    message = canonical_message(sender, receiver, amount, nonce, timestamp).encode("utf-8")
    try:
        with oqs.Signature(entry["algorithm"]) as verifier:
            ok = verifier.verify(
                message,
                base64.b64decode(signature_b64),
                base64.b64decode(entry["public_key"]),
            )
    except Exception:
        ok = False

    if ok:
        return {"status": "verified", "reason": "Signature valid"}
    return {"status": "invalid", "reason": "Signature does not match this transaction"}
