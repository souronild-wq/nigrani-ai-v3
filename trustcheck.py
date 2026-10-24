
def check_invoice(
    quantity,
    unit_price,
    market_price,
    budget,
    claimed_total,
    invoice_id="Unknown",
    supplier="Unknown",
    material="Unknown",
):
    """
    TrustCheck: explainable invoice verification.

    Identifies potential invoice irregularities for human review.
    The score represents review priority, not fraud probability.
    """

    findings = []
    checks_passed = []

    # 1. Validate numeric inputs.
    values = {
        "Quantity": quantity,
        "Unit price": unit_price,
        "Market price": market_price,
        "Budget": budget,
        "Claimed total": claimed_total,
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
            "findings": [
                {
                    "severity": "High",
                    "reason": (
                        "One or more fields contain "
                        "non-numeric values."
                    ),
                }
            ],
            "checks_passed": [],
            "review_required": True,
        }

    quantity = values["Quantity"]
    unit_price = values["Unit price"]
    market_price = values["Market price"]
    budget = values["Budget"]
    claimed_total = values["Claimed total"]

    # 2. Reject invalid numeric values.
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
            "findings": [
                {
                    "severity": "High",
                    "reason": (
                        "Quantity and reference values must "
                        "be positive. Price and total values "
                        "cannot be negative."
                    ),
                }
            ],
            "checks_passed": [],
            "review_required": True,
        }

    # 3. Calculate the expected total and price difference.
    expected_total = quantity * unit_price
    price_difference = unit_price - market_price
    price_ratio = unit_price / market_price

    # 4. Check whether the invoice total is correct.
    if abs(claimed_total - expected_total) > 0.01:
        findings.append(
            {
                "severity": "High",
                "reason": (
                    f"Total mismatch: claimed total is "
                    f"{claimed_total:.2f}, but quantity × "
                    f"unit price equals {expected_total:.2f}."
                ),
            }
        )
    else:
        checks_passed.append(
            "Invoice total matches quantity × unit price."
        )

    # 5. Compare unit price against the reference market price.
    if unit_price > market_price * 1.20:
        findings.append(
            {
                "severity": "High",
                "reason": (
                    f"Unit price is "
                    f"{((price_ratio - 1) * 100):.1f}% "
                    "above the reference market price."
                ),
            }
        )
    else:
        checks_passed.append(
            "Unit price is within the 20% review threshold."
        )

    # 6. Check whether the claimed total exceeds the budget.
    if claimed_total > budget:
        findings.append(
            {
                "severity": "High",
                "reason": (
                    "Claimed total exceeds the budget by "
                    f"{claimed_total - budget:.2f}."
                ),
            }
        )
    else:
        checks_passed.append(
            "Claimed total is within the budget."
        )

    # 7. Calculate the review-priority score.
    # Each finding adds 30 points, up to a maximum of 100.
    trust_score = min(len(findings) * 30, 100)

    if trust_score >= 60:
        status = "High Review Priority"
    elif trust_score >= 30:
        status = "Needs Review"
    else:
        status = "Passed Basic Checks"

    # 8. Return the results for the dashboard or tests.
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
        "review_required": len(findings) > 0,
    }
