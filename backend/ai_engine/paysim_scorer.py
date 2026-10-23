"""
paysim_scorer.py - secondary anomaly signal from the PaySim Isolation Forest.
Display-only: it does not change risk_level or trigger algorithm switches.
Model trained by backend/training/train_model.py (amount + type).
"""
import os

import numpy as np
import pandas as pd
import joblib

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "isolation_forest.joblib",
)
MODEL_NAME = "Isolation Forest (trained on PaySim)"

try:
    _bundle = joblib.load(MODEL_PATH)
    _model = _bundle["model"]
    _types = _bundle["types"]
    _s_min = _bundle["score_min"]
    _s_max = _bundle["score_max"]
    LOADED = True
except Exception as e:
    LOADED = False
    print(f"[PAYSIM] model not loaded ({e}); paysim_score will be None")


def paysim_score(amount: float, txn_type: str = "PAYMENT") -> dict:
    if not LOADED:
        return {"paysim_score": None, "paysim_model": None}
    row = {"log_amount": np.log1p(max(float(amount), 0.0))}
    for t in _types:
        row[f"type_{t}"] = 1 if txn_type.upper() == t else 0
    raw = -_model.score_samples(pd.DataFrame([row]))[0]
    score = float(np.clip((raw - _s_min) / (_s_max - _s_min), 0, 1))
    return {"paysim_score": round(score, 2), "paysim_model": MODEL_NAME}
