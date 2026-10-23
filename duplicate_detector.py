
import pandas as pd


def detect_duplicates(df):
    """
    Find duplicate invoice IDs and repeated invoice details.
    Returns a copy of the dataset with duplicate warnings.
    """

    required_columns = [
        "invoice_id",
        "supplier",
        "material",
        "quantity",
        "total_amount"
    ]

    # Check whether required columns exist
    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    # Work on a copy so the original dataset is not changed
    report = df.copy()

    # Check 1: Repeated invoice IDs
    invoice_ids = report["invoice_id"].astype(str).str.strip()

    report["duplicate_invoice_id"] = (
        invoice_ids.duplicated(keep=False)
    )

    # Check 2: Identical supplier, material, quantity and amount
    detail_columns = [
        "supplier",
        "material",
        "quantity",
        "total_amount"
    ]

    report["duplicate_details"] = report.duplicated(
        subset=detail_columns,
        keep=False
    )

    # Explain why each invoice was flagged
    reasons = []

    for _, row in report.iterrows():
        findings = []

        if row["duplicate_invoice_id"]:
            findings.append("Repeated invoice ID")

        if row["duplicate_details"]:
            findings.append("Repeated invoice details")

        if findings:
            reasons.append("; ".join(findings))
        else:
            reasons.append("No duplicate detected")

    report["duplicate_reason"] = reasons

    # Overall review flag
    report["duplicate_review_required"] = (
        report["duplicate_invoice_id"]
        | report["duplicate_details"]
    )

    return report


if __name__ == "__main__":
    print("NIGRANI AI - DUPLICATE DETECTOR")
    print("--------------------------------")

    try:
        # Read the existing invoice dataset
        df = pd.read_csv("transactions.csv")

        # Detect duplicates
        report = detect_duplicates(df)

        # Save results
        report.to_csv("duplicate_report.csv", index=False)

        # Display summary
        total = len(report)

        flagged = int(
            report["duplicate_review_required"].sum()
        )

        print(f"Total invoices checked: {total}")
        print(f"Invoices flagged for duplicate review: {flagged}")
        print("Report saved as duplicate_report.csv")

        if flagged > 0:
            print("\nFlagged invoices:")
            print(
                report.loc[
                    report["duplicate_review_required"],
                    [
                        "invoice_id",
                        "supplier",
                        "material",
                        "duplicate_reason"
                    ]
                ].to_string(index=False)
            )
        else:
            print(
                "\nNo duplicate records found in this dataset."
            )

        print("\nDuplicate detection completed!")

    except FileNotFoundError:
        print("ERROR: transactions.csv was not found.")
        print("Run this script from your nigrani-ai project folder.")

    except ValueError as error:
        print("ERROR:", error)
