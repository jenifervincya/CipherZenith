import time

REPLAY_WINDOW_SECONDS = 60

# Flip to True once the Flutter app and React dashboard send nonce + timestamp.
REQUIRE_FRESHNESS = False

# Keep nonces for 2x the window: a timestamp up to +60s in the future
# stays valid for up to 120s after we first accept it.
_NONCE_RETENTION_SECONDS = 2 * REPLAY_WINDOW_SECONDS

# "sender:nonce" -> time we first accepted it
_seen_nonces: dict[str, float] = {}


def check_freshness(sender: str, nonce: str | None, timestamp: float | None) -> dict:
    """
    Returns {"status": ..., "reason": ...} where status is one of:
      fresh      - nonce is new and timestamp is within the window
      replay     - this nonce was already used
      stale      - timestamp is too old (or too far in the future)
      invalid    - only one of nonce/timestamp supplied, or required but missing
      unchecked  - legacy client sent neither (allowed while REQUIRE_FRESHNESS is False)
    """
    if nonce is None and timestamp is None:
        if REQUIRE_FRESHNESS:
            return {"status": "invalid", "reason": "Nonce and timestamp are required"}
        return {"status": "unchecked", "reason": "No nonce/timestamp supplied (legacy client)"}

    if nonce is None or timestamp is None:
        return {"status": "invalid", "reason": "Both nonce and timestamp must be supplied together"}

    now = time.time()

    # Forget nonces we no longer need to remember
    for key in [k for k, seen_at in _seen_nonces.items()
                if now - seen_at > _NONCE_RETENTION_SECONDS]:
        del _seen_nonces[key]

    offset = now - timestamp
    if abs(offset) > REPLAY_WINDOW_SECONDS:
        return {
            "status": "stale",
            "reason": f"Timestamp is {round(offset)}s off the server clock "
                      f"(allowed +/-{REPLAY_WINDOW_SECONDS}s)"
        }

    key = f"{sender}:{nonce}"
    if key in _seen_nonces:
        return {"status": "replay", "reason": "Nonce already used"}

    _seen_nonces[key] = now
    return {"status": "fresh", "reason": "Nonce is new and timestamp is within window"}
