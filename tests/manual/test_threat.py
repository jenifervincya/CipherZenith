from ai_engine.threat_detection import detect_threat

test_transaction = {
    "sender": "Jeni",
    "receiver": "Mugunthan",
    "amount": 500
}

# Simulate a LOW anomaly score (like Step 3 would produce for a small amount)
result_low = detect_threat(test_transaction, anomaly_score=0.05)
print("Low anomaly result:", result_low)

# Simulate a HIGH anomaly score (like Step 3 would produce for a big amount)
result_high = detect_threat(test_transaction, anomaly_score=0.85)
print("High anomaly result:", result_high)