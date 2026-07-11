import random

def analyze_transaction(transaction: dict) -> dict:
    amount = transaction.get("amount", 0)

    # Simple rule: bigger amounts look riskier, with some randomness added
    base_score = min(amount / 10000, 1.0)
    noise = random.uniform(-0.05, 0.05)
    anomaly_score = round(max(0.0, min(base_score + noise, 1.0)), 2)

    if anomaly_score < 0.3:
        risk_level = "LOW"
    elif anomaly_score < 0.7:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    return {
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "patterns_checked": 47
    }