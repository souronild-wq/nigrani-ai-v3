

import pandas as pd
import random

# Make the dataset reproducible
random.seed(42)

# Sample materials and their reference market prices (₹)
materials = {
    "Cement": 400,
    "Steel": 65,
    "Bricks": 10,
    "Sand": 1800,
    "Paint": 250
}

# Sample suppliers
suppliers = [
    "ABC Suppliers",
    "BuildMart",
    "Prime Materials",
    "City Construction Supplies",
    "Reliable Traders"
]

transactions = []

# Generate 320 synthetic invoices
for i in range(1, 321):

    # First 300 invoices are normal
    # Last 20 invoices are deliberately overpriced for demonstration
    suspicious = i > 300

    material = random.choice(list(materials.keys()))
    market_price = materials[material]
    quantity = random.randint(10, 200)
    supplier = random.choice(suppliers)

    if suspicious:
        # Create an unusually high price for demo testing
        unit_price = round(
            market_price * random.uniform(1.5, 2.5), 2
        )
    else:
        # Normal price with small variation
        unit_price = round(
            market_price * random.uniform(0.95, 1.10), 2
        )

    total_amount = round(quantity * unit_price, 2)

    # Synthetic project budget
    budget = round(
        quantity * market_price * random.uniform(1.2, 2.0), 2
    )

    transactions.append({
        "invoice_id": f"INV{i:04d}",
        "supplier": supplier,
        "material": material,
        "quantity": quantity,
        "unit_price": unit_price,
        "market_price": market_price,
        "budget": budget,
        "total_amount": total_amount,
        "label": 1 if suspicious else 0
    })

# Convert data to a DataFrame
df = pd.DataFrame(transactions)

# Save the dataset
df.to_csv("transactions.csv", index=False)

print("NIGRANI AI - DATA GENERATION COMPLETE")
print("-------------------------------------")
print(f"Total invoices: {len(df)}")
print(f"Normal demo invoices: {(df['label'] == 0).sum()}")
print(f"Overpriced demo invoices: {(df['label'] == 1).sum()}")
print(f"Supplier column added: {'supplier' in df.columns}")
print("Dataset saved as transactions.csv")
print("\nFirst 5 invoices:")
print(df.head())
