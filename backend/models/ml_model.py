"""
ml_model.py - Isolation Forest anomaly scorer (Layer 3)

Scores how unusual a transaction is FOR THAT SENDER, from three signals:
  - amount
  - hour of day
  - per-sender history (amount relative to the sender's own running average)

Trained at startup on SYNTHETIC "normal" transactions (no real fraud data exists).
An unsupervised model learns what normal looks like and scores deviation from it.
"""
import math
from datetime import datetime, timedelta, timezone

import numpy as np
from sklearn.ensemble import IsolationForest

RANDOM_SEED = 42
N_SENDERS = 200
TXNS_PER_SENDER = 30

# Same thresholds monitor.py used before, so risk_level keeps its meaning.
MEDIUM_THRESHOLD = 0.3
HIGH_THRESHOLD = 0.7

# A sender needs this many past transactions before their own average is trusted.
MIN_HISTORY = 3

# Fixed offset instead of ZoneInfo: Windows has no tz database by default.
IST = timezone(timedelta(hours=5, minutes=30))

# sender -> {"count": n, "mean": running average amount}
_history: dict[str, dict] = {}

_model = None
_calibration = None  # (raw-score anchors, anomaly-score anchors) for np.interp


def _features(amount, hour, log_ratio):
    return [
        math.log1p(amount),
        math.sin(2 * math.pi * hour / 24),
        math.cos(2 * math.pi * hour / 24),
        log_ratio,
    ]


def _synthetic_normal_data():
    """200 senders, each with their own typical amount and mostly-daytime habits."""
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    sender_means = rng.lognormal(mean=math.log(1500), sigma=0.8, size=N_SENDERS)
    for sender_mean in sender_means:
        amounts = sender_mean * rng.lognormal(0.0, 0.35, size=TXNS_PER_SENDER)
        hours = np.floor(rng.normal(14, 3.5, size=TXNS_PER_SENDER)) % 24
        for amount, hour in zip(amounts, hours):
            rows.append(_features(amount, hour, math.log(amount / sender_mean)))
    return np.array(rows)


def _train():
    global _model, _calibration
    X = _synthetic_normal_data()
    _model = IsolationForest(n_estimators=200, random_state=RANDOM_SEED)
    _model.fit(X)

    # score_samples: higher = more normal. Flip it so higher = more anomalous.
    raw = -_model.score_samples(X)
    p50, p95, p99 = np.percentile(raw, [50, 95, 99])
    top = p99 + (p99 - p50)
    _calibration = ([p50, p95, p99, top], [0.10, 0.30, 0.70, 1.0])


def _update_history(sender, amount):
    entry = _history.setdefault(sender, {"count": 0, "mean": 0.0})
    entry["mean"] = (entry["mean"] * entry["count"] + amount) / (entry["count"] + 1)
    entry["count"] += 1


def score_transaction(sender, amount, hour=None, update_history=True):
    """
    Returns {"anomaly_score": 0..1, "risk_level": LOW|MEDIUM|HIGH, ...}.
    hour defaults to the current hour in IST.
    """
    if _model is None:
        _train()

    if hour is None:
        hour = datetime.now(IST).hour
    amount = max(float(amount), 0.0)

    entry = _history.get(sender)
    if entry and entry["count"] >= MIN_HISTORY and entry["mean"] > 0:
        log_ratio = math.log(max(amount, 1.0) / entry["mean"])
        history_used = True
    else:
        log_ratio = 0.0   # cold start: no trustworthy average yet
        history_used = False

    x = np.array([_features(amount, hour, log_ratio)])
    raw = float(-_model.score_samples(x)[0])
    xp, fp = _calibration
    anomaly_score = round(float(np.interp(raw, xp, fp)), 2)

    if anomaly_score < MEDIUM_THRESHOLD:
        risk_level = "LOW"
    elif anomaly_score < HIGH_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    # A flagged transaction must not teach the model that it is normal.
    if update_history and risk_level != "HIGH":
        _update_history(sender, amount)

    return {
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "raw_score": round(raw, 3),
        "history_used": history_used,
        "hour": hour,
    }


# -- Self-test: run `python backend/models/ml_model.py` from the repo root --------
if __name__ == "__main__":
    print("=" * 62)
    print("  CipherZenith - Isolation Forest self-test")
    print("=" * 62)

    failures = 0

    def check(name, ok):
        global failures
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures += 1

    _history.clear()
    for _ in range(5):
        score_transaction("regular", 1500, hour=14)   # build a normal history

    cases = [
        ("new sender, Rs 500, 2 PM",             dict(sender="newbie-1", amount=500,   hour=14)),
        ("new sender, Rs 50,000, 2 PM",          dict(sender="newbie-2", amount=50000, hour=14)),
        ("regular, Rs 1,500 (usual), 3 PM",      dict(sender="regular",  amount=1500,  hour=15)),
        ("regular, Rs 1,500 (usual), 3 AM",      dict(sender="regular",  amount=1500,  hour=3)),
        ("regular, Rs 15,000 (10x usual), 2 PM", dict(sender="regular",  amount=15000, hour=14)),
        ("regular, Rs 50,000 (33x usual), 2 PM", dict(sender="regular",  amount=50000, hour=14)),
        ("regular, Rs 90,000, 3 AM",             dict(sender="regular",  amount=90000, hour=3)),
    ]

    print("\n  scenario                                score  level   history")
    results = {}
    for name, kwargs in cases:
        r = score_transaction(**kwargs, update_history=False)
        results[name] = r
        print(f"  {name:<38}  {r['anomaly_score']:<5}  {r['risk_level']:<6}  {r['history_used']}")

    print()
    check("usual amount, daytime -> LOW",
          results["regular, Rs 1,500 (usual), 3 PM"]["risk_level"] == "LOW")
    check("new sender, small amount -> not HIGH",
          results["new sender, Rs 500, 2 PM"]["risk_level"] != "HIGH")
    check("new sender: Rs 50,000 scores above Rs 500 (order preserved)",
          results["new sender, Rs 50,000, 2 PM"]["anomaly_score"]
          > results["new sender, Rs 500, 2 PM"]["anomaly_score"])
    check("regular sender's sudden 33x jump (Rs 50,000 vs Rs 1,500 usual) -> HIGH",
          results["regular, Rs 50,000 (33x usual), 2 PM"]["risk_level"] == "HIGH")
    check("10x the sender's usual amount -> HIGH",
          results["regular, Rs 15,000 (10x usual), 2 PM"]["risk_level"] == "HIGH")
    check("Rs 90,000 at 3 AM -> HIGH",
          results["regular, Rs 90,000, 3 AM"]["risk_level"] == "HIGH")
    check("same amount scores higher at 3 AM than 3 PM",
          results["regular, Rs 1,500 (usual), 3 AM"]["anomaly_score"]
          > results["regular, Rs 1,500 (usual), 3 PM"]["anomaly_score"])

    before = dict(_history["regular"])
    score_transaction("regular", 90000, hour=3, update_history=True)
    check("a HIGH transaction does not change the sender's history",
          _history["regular"] == before)

    print("\n" + "=" * 62)
    print("  All checks passed" if failures == 0 else f"  {failures} check(s) FAILED")
    print("=" * 62)
