
from trustcheck import check_invoice

# Test 1: A normal invoice
normal = check_invoice(
    quantity=10,
    unit_price=100,
    market_price=100,
    budget=1500,
    claimed_total=1000,
    invoice_id="INV001",
    supplier="ABC Suppliers",
    material="Steel"
)

print("NORMAL INVOICE")
print("Status:", normal["status"])
print("Trust score:", normal["trust_score"])
print("Review required:", normal["review_required"])

# Test 2: An invoice with suspicious details
suspicious = check_invoice(
    quantity=100,
    unit_price=600,
    market_price=400,
    budget=50000,
    claimed_total=70000,
    invoice_id="INV002",
    supplier="Unknown Supplier",
    material="Cement"
)

print("\nSUSPICIOUS INVOICE")
print("Status:", suspicious["status"])
print("Trust score:", suspicious["trust_score"])
print("Review required:", suspicious["review_required"])

for finding in suspicious["findings"]:
    print("-", finding["reason"])
