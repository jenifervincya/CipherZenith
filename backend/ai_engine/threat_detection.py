import random

FORCE_THREAT_DEMO = False

THREAT_TYPES = ["Replay Attack", "Man-in-the-Middle", "Unusual Access Pattern"]

def detect_threat(transaction: dict, anomaly_score: float) -> dict:
    if FORCE_THREAT_DEMO:
        return {
            "threat_found": True,
            "threat_type": "Replay Attack",
            "confidence": 87.0
        }

    # Natural mode: higher anomaly score = higher chance of a "threat"
    threat_found = anomaly_score > 0.7

    if threat_found:
        threat_type = random.choice(THREAT_TYPES)
        confidence = round(random.uniform(75.0, 95.0), 1)
    else:
        threat_type = None
        confidence = round(random.uniform(95.0, 99.9), 1)

    return {
        "threat_found": threat_found,
        "threat_type": threat_type,
        "confidence": confidence
    }