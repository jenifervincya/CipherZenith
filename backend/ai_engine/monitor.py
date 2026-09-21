from models.ml_model import score_transaction


def analyze_transaction(transaction: dict, update_history: bool = True) -> dict:
    """
    Step 3: score how unusual this transaction is FOR THIS SENDER
    (Isolation Forest on amount, hour of day and the sender's own history).
    """
    result = score_transaction(
        sender=transaction.get("sender", "unknown"),
        amount=transaction.get("amount", 0),
        update_history=update_history,
    )

    return {
        "anomaly_score": result["anomaly_score"],
        "risk_level": result["risk_level"],
        # Number of signals the model scores (amount, hour sin, hour cos, sender ratio).
        # Was a hard-coded 47 before; the key stays so the dashboard still renders.
        "patterns_checked": 4,
        "history_used": result["history_used"],
    }
