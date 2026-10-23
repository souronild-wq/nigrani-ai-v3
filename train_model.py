
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest

print("Loading invoice dataset...")

df = pd.read_csv("transactions.csv")

# Calculate useful financial features
df["price_ratio"] = df["unit_price"] / df["market_price"]
df["budget_usage"] = df["total_amount"] / df["budget"]

features = [
    "unit_price",
    "market_price",
    "quantity",
    "price_ratio",
    "budget_usage",
    "total_amount"
]

# Train only on normal invoices
normal_data = df[df["label"] == 0][features]

print("Training Isolation Forest model...")

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

model.fit(normal_data)

# Save the trained model and feature names
with open("nigrani_model.pkl", "wb") as file:
    pickle.dump(
        {"model": model, "features": features},
        file
    )

print("Model training completed successfully!")
print("Model saved as nigrani_model.pkl")
print(f"Training invoices: {len(normal_data)}")
print("Algorithm: Isolation Forest")
