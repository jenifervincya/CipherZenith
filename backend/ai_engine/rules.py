"""
rules.py - Layer 2 rule checks (velocity, new receiver, large first transaction)

Sits beside the anomaly model. Cheap, fast and explainable, and it catches
what the model cannot: request rate, and a first-time large transfer from a
sender with no history. State is in memory and resets on restart.
"""
import time
from collections import deque

VELOCITY_WINDOW_SECONDS = 60
VELOCITY_LIMIT = 5             # more than this many in the window is flagged
LARGE_FIRST_TXN = 20000        # a new sender's first transfer at or above this is flagged
NEW_RECEIVER_AMOUNT = 10000    # first payment to a new receiver at or above this is flagged

_recent: dict[str, deque] = {}          # sender -> timestamps of recent attempts
_known_receivers: dict[str, set] = {}   # sender -> receivers paid without a flag


def reset_state():
    _recent.clear()
    _known_receivers.clear()


def check_rules(sender, receiver, amount, now=None):
    """Returns {"threat_found": bool, "flags": [{"rule", "reason"}], "rules_checked": 3}."""
    now = time.time() if now is None else now
    amount = float(amount)
    flags = []

    # Rule 1: velocity. Every attempt counts, flagged or not.
    window = _recent.setdefault(sender, deque())
    while window and now - window[0] > VELOCITY_WINDOW_SECONDS:
        window.popleft()
    window.append(now)
    if len(window) > VELOCITY_LIMIT:
        flags.append({
            "rule": "Velocity Limit Exceeded",
            "reason": f"{len(window)} transactions in {VELOCITY_WINDOW_SECONDS}s "
                      f"(limit {VELOCITY_LIMIT})",
        })

    # Rules 2 and 3: receiver history
    known = _known_receivers.get(sender)
    if known is None:
        if amount >= LARGE_FIRST_TXN:
            flags.append({
                "rule": "Large First Transaction",
                "reason": f"First transaction from this sender is Rs {amount:,.0f} "
                          f"(threshold Rs {LARGE_FIRST_TXN:,})",
            })
    elif receiver not in known and amount >= NEW_RECEIVER_AMOUNT:
        flags.append({
            "rule": "New Receiver, High Amount",
            "reason": f"First payment to '{receiver}' is Rs {amount:,.0f} "
                      f"(threshold Rs {NEW_RECEIVER_AMOUNT:,})",
        })

    # A flagged transaction must not teach the rules that its receiver is normal.
    if not flags:
        _known_receivers.setdefault(sender, set()).add(receiver)

    return {"threat_found": bool(flags), "flags": flags, "rules_checked": 3}


# -- Self-test: run `python backend/ai_engine/rules.py` from the repo root ----------
if __name__ == "__main__":
    print("=" * 62)
    print("  CipherZenith - Layer 2 rules self-test")
    print("=" * 62)

    failures = 0

    def check(name, ok):
        global failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures += 1

    def names(result):
        return [f["rule"] for f in result["flags"]]

    T0 = 1_000_000.0

    reset_state()
    check("new sender, Rs 500 -> no flags",
          not check_rules("a", "r1", 500, now=T0)["threat_found"])

    reset_state()
    check("new sender, first Rs 50,000 -> Large First Transaction",
          names(check_rules("b", "r1", 50000, now=T0)) == ["Large First Transaction"])

    reset_state()
    check_rules("c", "r1", 1500, now=T0)
    check("known sender, known receiver, Rs 1,500 -> no flags",
          not check_rules("c", "r1", 1500, now=T0 + 1)["threat_found"])
    check("known sender, new receiver, Rs 500 -> no flags",
          not check_rules("c", "r2", 500, now=T0 + 2)["threat_found"])
    check("known sender, new receiver, Rs 15,000 -> New Receiver, High Amount",
          names(check_rules("c", "r3", 15000, now=T0 + 3)) == ["New Receiver, High Amount"])
    check("flagged receiver was not learned: same payment is flagged again",
          names(check_rules("c", "r3", 15000, now=T0 + 4)) == ["New Receiver, High Amount"])

    reset_state()
    check_rules("d", "r1", 50000, now=T0)
    check("flagged first transaction was not learned: still flagged",
          names(check_rules("d", "r1", 50000, now=T0 + 1)) == ["Large First Transaction"])

    reset_state()
    results = [check_rules("e", "r1", 100, now=T0 + i) for i in range(6)]
    check("5 transactions in 60s -> not flagged",
          not any(r["threat_found"] for r in results[:5]))
    check("6th transaction in 60s -> Velocity Limit Exceeded",
          names(results[5]) == ["Velocity Limit Exceeded"])
    check("after the window passes -> not flagged again",
          not check_rules("e", "r1", 100, now=T0 + 200)["threat_found"])

    print("\n" + "=" * 62)
    print("  All checks passed" if failures == 0 else f"  {failures} check(s) FAILED")
    print("=" * 62)
