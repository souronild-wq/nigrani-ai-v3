
import pandas as pd


def detect_duplicate_invoices(df):
    """
    Flag invoices with repeated invoice IDs or
    matching supplier, material, quantity and amount.
    """

    required_columns = [
        "invoice_id",
        "supplier",
        "material",
        "quantity",
        "total_amount"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing columns: " + ", ".join(missing)
        )

    result = df.copy()

    result["duplicate_id"] = (
        result["invoice_id"].duplicated(keep=False)
    )

    # A matching invoice fingerprint is a review signal,
    # not proof that a payment was duplicated.
    fingerprint = [
        "supplier",
        "material",
        "quantity",
        "total_amount"
    ]

    result["duplicate_details"] = (
        result.duplicated(
            subset=fingerprint,
            keep=False
        )
    )

    result["duplicate_review"] = (
        result["duplicate_id"]
        | result["duplicate_details"]
    )

    return result


if __name__ == "__main__":
    demo = pd.DataFrame([
        {
            "invoice_id": "INV-001",
            "supplier": "BuildCo",
            "material": "Cement",
            "quantity": 100,
            "total_amount": 40000
        },
        {
            "invoice_id": "INV-002",
            "supplier": "BuildCo",
            "material": "Cement",
            "quantity": 100,
            "total_amount": 40000
        },
        {
            "invoice_id": "INV-003",
            "supplier": "StoneWorks",
            "material": "Steel",
            "quantity": 50,
            "total_amount": 3250
        }
    ])

    checked = detect_duplicate_invoices(demo)

    print(checked[
        ["invoice_id", "duplicate_review"]
    ].to_string(index=False))
