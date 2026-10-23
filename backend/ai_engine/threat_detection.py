from backend.models.ml_model import HIGH_THRESHOLD

# Demo switch: True forces a threat so judges can see Kyber512 -> Kyber1024.
# Keep False for normal runs.
FORCE_THREAT_DEMO = False


def detect_threat(transaction: dict, anomaly_score: float) -> dict:
    """
    Step 4: turn the Step 3 anomaly score into a verdict.

    Replay, stale timestamps and forged signatures are rejected earlier, by the
    freshness and signature checks in main.py. What reaches this step is
    "behaviour that is unusual for this sender", so that is all we claim.
    """
    if FORCE_THREAT_DEMO:
        return {
            "threat_found": True,
            "threat_type": "Anomalous Behaviour",
            "confidence": 87.0,
            "detected_by": "demo_mode",
            "reason": "DEMO MODE: threat forced to show the algorithm switch",
        }

    threat_found = anomaly_score >= HIGH_THRESHOLD

    if threat_found:
        return {
            "threat_found": True,
            "threat_type": "Anomalous Behaviour",
            # Model risk score as a percentage, not a calibrated probability.
            "confidence": round(anomaly_score * 100, 1),
            "detected_by": "anomaly_model",
            "reason": f"Anomaly score {anomaly_score} reached the HIGH threshold ({HIGH_THRESHOLD})",
        }

    return {
        "threat_found": False,
        "threat_type": None,
        "confidence": round((1 - anomaly_score) * 100, 1),
        "detected_by": "anomaly_model",
        "reason": f"Anomaly score {anomaly_score} is below the HIGH threshold ({HIGH_THRESHOLD})",
    }