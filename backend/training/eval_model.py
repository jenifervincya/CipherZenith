"""
eval_model.py - evaluate the saved model at the thresholds the app uses.
Run from the backend/ folder:  python training/eval_model.py
"""
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, precision_score, recall_score

CSV_PATH = "data/paysim.csv"
MODEL_PATH = "models/isolation_forest.joblib"
SEED = 7  # different from training seed

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
types = bundle["types"]
s_min, s_max = bundle["score_min"], bundle["score_max"]


def make_features(df):
    feats = pd.DataFrame({"log_amount": np.log1p(df["amount"])})
    for t in types:
        feats[f"type_{t}"] = (df["type"] == t).astype(int)
    return feats


df = pd.read_csv(CSV_PATH, usecols=["type", "amount", "isFraud"])
normal = df[df["isFraud"] == 0].sample(n=100_000, random_state=SEED)
fraud = df[df["isFraud"] == 1]
test = pd.concat([normal, fraud])
y = test["isFraud"].values

raw = -model.score_samples(make_features(test))
scaled = np.clip((raw - s_min) / (s_max - s_min), 0, 1)

print("=" * 55)
print("  Evaluation at app thresholds")
print("=" * 55)
print(f"AUC (threshold-free): {roc_auc_score(y, scaled):.3f}")
print(f"Scaled score - normal median: {np.median(scaled[y == 0]):.2f}")
print(f"Scaled score - fraud median : {np.median(scaled[y == 1]):.2f}")

for thr, label in [(0.3, "MEDIUM or higher"), (0.7, "HIGH")]:
    pred = (scaled >= thr).astype(int)
    fpr = pred[y == 0].mean()
    print(f"\nThreshold {thr} ({label}):")
    print(f"  Precision : {precision_score(y, pred, zero_division=0):.3f}")
    print(f"  Recall    : {recall_score(y, pred):.3f}")
    print(f"  False alarm rate on normal: {fpr:.1%}")