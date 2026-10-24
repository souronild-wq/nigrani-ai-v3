
def check_invoice(
    quantity,
    unit_price,
    market_price,
    budget,
    claimed_total,
    invoice_id="Unknown",
    supplier="Unknown",
    material="Unknown"
):
    """
    TrustCheck: explainable invoice verification.
    Flags suspicious details for human review.
    It does not determine whether fraud has occurred.
    """

    findings = []
    checks_passed = []

    # 1. Validate numeric inputs
    values = {
        "Quantity": quantity,
        "Unit price": unit_price,
        "Market price": market_price,
        "Budget": budget,
        "Claimed total": claimed_total
    }

    try:
        values = {
            name: float(value)
            for name, value in values.items()
        }
    except (TypeError, ValueError):
        return {
            "invoice_id": invoice_id,
            "supplier": supplier,
            "material": material,
            "status": "Invalid Data",
            "trust_score": 0,
            "findings": [{
                "severity": "High",
                "reason": "One or more fields contain non-numeric values."
            }],
            "checks_passed": [],
            "review_required": True
        }

    quantity = values["Quantity"]
    unit_price = values["Unit price"]
    market_price = values["Market price"]
    budget = values["Budget"]
    claimed_total = values["Claimed total"]

    # 2. Reject impossible or invalid values
    if (
        quantity <= 0
        or unit_price < 0
        or market_price <= 0
        or budget <= 0
        or claimed_total < 0
    ):
        return {
            "invoice_id": invoice_id,
            "supplier": supplier,
            "material": material,
            "status": "Invalid Data",
            "trust_score": 0,
            "findings": [{
                "severity": "High",
                "reason": (
                    "Quantity and reference values must be positive. "
                    "Price and total values cannot be negative."
                )
            }],
            "checks_passed": [],
            "review_required": True
        }

    # 3. Calculate expected total
    expected_total = quantity * unit_price
    price_difference = unit_price - market_price
    price_ratio = unit_price / market_price

    # 4. Check whether the claimed total matches the calculation
    if abs(claimed_total - expected_total) > 0.01:
        findings.append({
            "severity": "High",
            "reason": (
                f"Total mismatch: claimed total is "
                f"{claimed_total:.2f}, but quantity × unit price "
                f"equals {expected_total:.2f}."
            )
        })
    else:
        checks_passed.append("Invoice total matches quantity × unit price.")

    # 5. Check price against the market reference
    if unit_price > market_price * 1.20:
        findings.append({
            "severity": "High",
            "reason": (
                f"Unit price is {((price_ratio - 1) * 100):.1f}% "
                f"above the reference market price."
            )
        })
    else:
        checks_passed.append("Unit price is within the 20% review threshold.")

    # 6. Check the budget
    if claimed_total > budget:
        findings.append({
            "severity": "High",
            "reason": (
                f"Claimed total exceeds the budget by "
                f"{claimed_total - budget:.2f}."
            )
        })
    else:
        checks_passed.append("Claimed total is within the budget.")

    # 7. Calculate a transparent TrustCheck score
    # Each triggered check contributes 1 point.
    # This is a review-priority score, not a fraud probability.
    trust_score = min(len(findings) * 30, 100)

    if trust_score >= 60:
        status = "High Review Priority"
    elif trust_score >= 30:
        status = "Needs Review"
    else:
        status = "Passed Basic Checks"

    return {
        "invoice_id": invoice_id,
        "supplier": supplier,
        "material": material,
        "expected_total": round(expected_total, 2),
        "claimed_total": round(claimed_total, 2),
        "price_difference": round(price_difference, 2),
        "price_ratio": round(price_ratio, 3),
        "trust_score": trust_score,
        "status": status,
        "findings": findings,
        "checks_passed": checks_passed,
        "review_required": len(findings) > 0
    }
