
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
    risk_factors = []
    risk_score = 0

    # Rule 1: Price is over 20% above the reference price
    if price_ratio > 1.20:
        points = 30
        risk_score += points

        findings.append(
            f"Unit price is {(price_ratio - 1) * 100:.1f}% "
            "above the reference price."
        )

        risk_factors.append({
            "factor": "Price above reference",
            "points": points,
            "reason": (
                f"Unit price is {(price_ratio - 1) * 100:.1f}% "
                "above the reference price."
            )
        })

    # Rule 2: Invoice total exceeds budget
    if claimed_total > budget:
        points = 25
        risk_score += points

        findings.append(
            f"Invoice exceeds budget by "
            f"Rs. {claimed_total - budget:,.2f}."
        )

        risk_factors.append({
            "factor": "Budget exceeded",
            "points": points,
            "reason": (
                f"Invoice exceeds budget by "
                f"Rs. {claimed_total - budget:,.2f}."
            )
        })

    # Rule 3: Claimed total doesn't match quantity x unit price
    if abs(claimed_total - expected_total) > 0.01:
        points = 25
        risk_score += points

        findings.append(
            f"Total mismatch: expected Rs. {expected_total:,.2f}, "
            f"but invoice claims Rs. {claimed_total:,.2f}."
        )

        risk_factors.append({
            "factor": "Total mismatch",
            "points": points,
            "reason": (
                f"Expected Rs. {expected_total:,.2f}, "
                f"but the claimed total is Rs. {claimed_total:,.2f}."
            )
        })

    # Rule 4: Machine-learning anomaly
    if ml_anomaly:
        points = 20
        risk_score += points

        risk_factors.append({
            "factor": "ML anomaly",
            "points": points,
            "reason": (
                "The trained model identified this transaction "
                "as unusual compared with its training data."
            )
        })

    # Keep score within 0-100
    risk_score = min(risk_score, 100)

    # Assign a risk category
    if risk_score >= 75:
        risk_level = "Critical"
    elif risk_score >= 50:
        risk_level = "High"
    elif risk_score >= 25:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Preserve the existing review logic
    review_needed = bool(findings) or ml_anomaly

    return {
        "review_needed": review_needed,
        "ml_anomaly": ml_anomaly,
        "findings": findings,
        "expected_total": expected_total,
        "price_difference": quantity * (unit_price - market_price),
        "price_ratio": price_ratio,
        "budget_usage": budget_usage,

        # New explainable risk-scoring fields
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
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
    print("Risk score:", result["risk_score"], "/ 100")
    print("Risk level:", result["risk_level"])
    print("Findings:")

    for finding in result["findings"]:
        print("-", finding)

    print("\nRisk factors:")
    for factor in result["risk_factors"]:
        print(
            f"- {factor['factor']}: +{factor['points']} points"
        )
        print(" ", factor["reason"])
