from ai_engine.monitor import analyze_transaction
from ai_engine.threat_detection import detect_threat
from ai_engine.adaptive_engine import decide_encryption

test_transaction = {
    "sender": "Jeni",
    "receiver": "Mugunthan",
    "amount": 9000
}

# Step 3
monitor_result = analyze_transaction(test_transaction)
print("Step 3 (Monitor):", monitor_result)

# Step 4 — uses Step 3's anomaly_score
threat_result = detect_threat(test_transaction, monitor_result["anomaly_score"])
print("Step 4 (Threat Detection):", threat_result)

# Step 5 — uses Step 3's risk_level AND Step 4's threat info
adaptive_result = decide_encryption(
    monitor_result["risk_level"],
    threat_result["threat_found"],
    threat_result["threat_type"]
)
print("Step 5 (Adaptive Engine):", adaptive_result)