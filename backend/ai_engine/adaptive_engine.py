def decide_encryption(risk_level: str, threat_found: bool, threat_type: str | None) -> dict:
    if threat_found or risk_level == "HIGH":
        decision = "SWITCH"
        algorithm_selected = "Kyber1024"
        if threat_found:
            reason = f"Escalated due to detected threat: {threat_type}"
        else:
            reason = "Escalated due to HIGH risk level"

    elif risk_level == "MEDIUM":
        decision = "MAINTAIN"
        algorithm_selected = "AES-256 + Kyber512"
        reason = "MEDIUM risk — maintaining hybrid encryption with closer monitoring"

    else:
        decision = "MAINTAIN"
        algorithm_selected = "AES-256 + Kyber512"
        reason = "LOW risk, no threat detected — standard hybrid encryption sufficient"

    return {
        "decision": decision,
        "algorithm_selected": algorithm_selected,
        "reason": reason
    }