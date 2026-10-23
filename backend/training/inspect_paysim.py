"""
inspect_paysim.py - look at PaySim before training anything.
Run from the backend/ folder:  python training/inspect_paysim.py
"""
import pandas as pd

CSV_PATH = "data/paysim.csv"

df = pd.read_csv(CSV_PATH)

print("=" * 55)
print("  PaySim inspection")
print("=" * 55)

print(f"\n[1] Rows: {len(df):,}")
print(f"    Columns: {list(df.columns)}")

print("\n[2] Transaction types (count):")
print(df["type"].value_counts().to_string())

print("\n[3] Fraud overall:")
fraud_count = int(df["isFraud"].sum())
print(f"    Fraud rows: {fraud_count:,} ({fraud_count / len(df):.4%})")

print("\n[4] Fraud by type:")
print(df.groupby("type")["isFraud"].sum().to_string())

print("\n[5] Amount: normal vs fraud")
print(df.groupby("isFraud")["amount"].describe().round(2).to_string())

print("\n[6] Sender repeat check (do senders appear more than once?)")
per_sender = df["nameOrig"].value_counts()
print(f"    Unique senders: {len(per_sender):,}")
print(f"    Senders with 2+ transactions: {(per_sender > 1).sum():,}")
print(f"    Max transactions by one sender: {per_sender.max()}")

print("\n[7] Time column 'step' (1 step = 1 hour)")
print(f"    Range: {df['step'].min()} to {df['step'].max()}")

print("\nDone.")