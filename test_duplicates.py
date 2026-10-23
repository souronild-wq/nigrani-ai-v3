
import pandas as pd
from duplicate_detector import detect_duplicates

# Create a small test dataset with one duplicate
test_data = pd.DataFrame([
    {
        "invoice_id": "INV001",
        "supplier": "ABC Suppliers",
        "material": "Cement",
        "quantity": 100,
        "total_amount": 40000
    },
    {
        "invoice_id": "INV001",
        "supplier": "ABC Suppliers",
        "material": "Cement",
        "quantity": 100,
        "total_amount": 40000
    },
    {
        "invoice_id": "INV003",
        "supplier": "BuildMart",
        "material": "Steel",
        "quantity": 50,
        "total_amount": 3250
    }
])

report = detect_duplicates(test_data)

print("\nDUPLICATE DETECTION TEST")
print("------------------------")

print(
    report[
        [
            "invoice_id",
            "duplicate_invoice_id",
            "duplicate_details",
            "duplicate_reason",
            "duplicate_review_required"
        ]
    ].to_string(index=False)
)

flagged = int(report["duplicate_review_required"].sum())

print(f"\nInvoices flagged: {flagged} out of {len(report)}")

if flagged == 2:
    print("TEST PASSED: Both duplicate records were detected.")
else:
    print("TEST FAILED: Please check the detector.")
