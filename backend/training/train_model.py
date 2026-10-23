"""
train_model.py - train an Isolation Forest on PaySim (amount + type).
Run from the backend/ folder:  python training/train_model.py
"""
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score

CSV_PATH = "data/paysim.csv"
MODEL_PATH = "models/isolation_forest.joblib"
SEED = 42
TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Same features must be built at runtime in monitor.py."""
    feats = pd.DataFrame({"log_amount": np.log1p(df["amount"])})
    for t in TYPES:
        feats[f"type_{t}"] = (df["type"] == t).astype(int)
    return feats


df = pd.read_csv(CSV_PATH, usecols=["type", "amount", "isFraud"])

normal = df[df["isFraud"] == 0]
fraud = df[df["isFraud"] == 1]

# Train on normal rows only (sample 200k)
train = normal.sample(n=200_000, random_state=SEED)

# Test set: held-out normal rows + all fraud rows
test_normal = normal.drop(train.index).sample(n=100_000, random_state=SEED)
test = pd.concat([test_normal, fraud])

model = IsolationForest(
    n_estimators=100,
    contamination="auto",
    random_state=SEED,
    n_jobs=-1,
)
model.fit(make_features(train))

# Evaluate: predict() gives -1 = anomaly, 1 = normal
pred = (model.predict(make_features(test)) == -1).astype(int)
y_true = test["isFraud"].values

print("=" * 55)
print("  Isolation Forest evaluation (PaySim)")
print("=" * 55)
print(f"Train rows : {len(train):,} (normal only)")
print(f"Test rows  : {len(test):,} ({int(y_true.sum()):,} fraud)")
print(f"Precision  : {precision_score(y_true, pred):.3f}")
print(f"Recall     : {recall_score(y_true, pred):.3f}")

# Save the model plus the training score range (needed to scale to 0-1)
scores = -model.score_samples(make_features(train))
os.makedirs("models", exist_ok=True)
joblib.dump(
    {
        "model": model,
        "types": TYPES,
        "score_min": float(np.percentile(scores, 1)),
        "score_max": float(np.percentile(scores, 99.9)),
    },
    MODEL_PATH,
)
print(f"\nSaved model to {MODEL_PATH}")