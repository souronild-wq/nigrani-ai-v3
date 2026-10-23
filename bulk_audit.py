

import pandas as pd
from detector import analyze_transaction
from duplicate_detector import detect_duplicates


def audit_csv(file):
    """Audit invoices for price, budget and duplicate warnings."""

    df = pd.read_csv(file)

    required_columns = [
        "invoice_id",
        "quantity",
        "unit_price",
        "market_price",
        "budget",
        "total_amount"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "CSV is missing required columns: "
            + ", ".join(missing)
        )

    # Run duplicate detection when supplier information is available
    if "supplier" in df.columns and "material" in df.columns:
        duplicate_report = detect_duplicates(df)
    else:
        duplicate_report = pd.DataFrame({
            "duplicate_invoice_id": [False] * len(df),
            "duplicate_details": [False] * len(df),
            "duplicate_reason": [
                "Duplicate check skipped: supplier or material missing"
            ] * len(df),
            "duplicate_review_required": [False] * len(df)
        })

    results = []

    for index, row in df.iterrows():

        result = analyze_transaction(
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            market_price=row["market_price"],
            budget=row["budget"],
            claimed_total=row["total_amount"]
        )

        duplicate_flag = bool(
            duplicate_report.iloc[index][
                "duplicate_review_required"
            ]
        )

        # Combine price/budget findings with duplicate warnings
        findings = list(result["findings"])

        if duplicate_flag:
            findings.append(
                "Duplicate warning: "
                + duplicate_report.iloc[index]["duplicate_reason"]
            )

        review_required = (
            bool(result["review_needed"]) or duplicate_flag
        )

        results.append({
            "invoice_id": row["invoice_id"],
            "supplier": row["supplier"]
                if "supplier" in df.columns else "Unknown",
            "material": row["material"]
                if "material" in df.columns else "Unknown",
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
            "market_price": row["market_price"],
            "budget": row["budget"],
            "total_amount": row["total_amount"],
            "review_required": review_required,
            "ml_anomaly": bool(result["ml_anomaly"]),
            "price_ratio": result["price_ratio"],
            "budget_usage_percent": (
                result["budget_usage"] * 100
            ),
            "duplicate_invoice_id": bool(
                duplicate_report.iloc[index][
                    "duplicate_invoice_id"
                ]
            ),
            "duplicate_details": bool(
                duplicate_report.iloc[index]["duplicate_details"]
            ),
            "duplicate_review_required": duplicate_flag,
            "duplicate_reason": duplicate_report.iloc[index][
                "duplicate_reason"
            ],
            "findings": "; ".join(findings)
        })

    report = pd.DataFrame(results)

    # Save a copy of the combined report
    report.to_csv("audit_report.csv", index=False)

    print("Combined audit completed!")
    print(f"Invoices analyzed: {len(report)}")
    print(
        "Invoices requiring review: "
        f"{int(report['review_required'].sum())}"
    )
    print(
        "Duplicate warnings: "
        f"{int(report['duplicate_review_required'].sum())}"
    )
    print("Report saved as audit_report.csv")

    return report


if __name__ == "__main__":
    audit_csv("transactions.csv")
