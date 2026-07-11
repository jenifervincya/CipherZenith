from ai_engine.monitor import analyze_transaction

test_transaction = {
    "sender": "Jeni",
    "receiver": "Mugunthan",
    "amount": 500
}

result = analyze_transaction(test_transaction)
print(result)