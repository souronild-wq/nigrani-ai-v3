
import pickle
import pandas as pd

# Load the trained model
with open("nigrani_model.pkl", "rb") as file:
    saved_data = pickle.load(file)

model = saved_data["model"]
features = saved_data["features"]


def analyze_transaction(
    quantity,
    unit_price,
    market_price,
    budget,
    claimed_total
):
    # Validate inputs
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if unit_price <= 0 or market_price <= 0:
        raise ValueError("Prices must be greater than zero.")

    if budget <= 0 or claimed_total <= 0:
        raise ValueError("Budget and total must be greater than zero.")

    # Calculate financial values
    expected_total = quantity * unit_price
    price_ratio = unit_price / market_price
    budget_usage = claimed_total / budget

    # Prepare features for the ML model
    invoice = pd.DataFrame([{
        "unit_price": unit_price,
        "market_price": market_price,
        "quantity": quantity,
        "price_ratio": price_ratio,
        "budget_usage": budget_usage,
        "total_amount": claimed_total
    }])

    invoice = invoice[features]

    # Predict whether the transaction looks unusual
    prediction = model.predict(invoice)[0]
    ml_anomaly = prediction == -1

    findings = []

    # Rule 1: Price is over 20% above the reference price
    if price_ratio > 1.20:
        findings.append(
            f"Unit price is {(price_ratio - 1) * 100:.1f}% "
            "above the reference price."
        )

    # Rule 2: Invoice total exceeds budget
    if claimed_total > budget:
        findings.append(
            f"Invoice exceeds budget by "
            f"₹{claimed_total - budget:,.2f}."
        )

    # Rule 3: Claimed total doesn't match quantity × unit price
    if abs(claimed_total - expected_total) > 0.01:
        findings.append(
            f"Total mismatch: expected ₹{expected_total:,.2f}, "
            f"but invoice claims ₹{claimed_total:,.2f}."
        )

    # Combine rule checks and model output
    review_needed = bool(findings) or ml_anomaly

    return {
        "review_needed": review_needed,
        "ml_anomaly": ml_anomaly,
        "findings": findings,
        "expected_total": expected_total,
        "price_difference": quantity * (unit_price - market_price),
        "price_ratio": price_ratio,
        "budget_usage": budget_usage
    }


# Quick test when this file is run directly
if __name__ == "__main__":
    result = analyze_transaction(
        quantity=100,
        unit_price=900,
        market_price=400,
        budget=50000,
        claimed_total=90000
    )

    print("\nNIGRANI AI - DETECTOR TEST")
    print("Review required:", result["review_needed"])
    print("ML anomaly:", result["ml_anomaly"])
    print("Findings:")

    for finding in result["findings"]:
        print("-", finding)
