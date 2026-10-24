
from trustcheck import check_invoice


def test_normal_invoice():
    """A normal invoice should pass all basic checks."""

    result = check_invoice(
        quantity=10,
        unit_price=100,
        market_price=100,
        budget=1500,
        claimed_total=1000,
        invoice_id="INV001",
        supplier="ABC Suppliers",
        material="Steel",
    )

    assert result["status"] == "Passed Basic Checks"
    assert result["trust_score"] == 0
    assert result["review_required"] is False
    assert len(result["findings"]) == 0


def test_suspicious_invoice():
    """An invoice with three irregularities should be flagged."""

    result = check_invoice(
        quantity=100,
        unit_price=600,
        market_price=400,
        budget=50000,
        claimed_total=70000,
        invoice_id="INV002",
        supplier="Unknown Supplier",
        material="Cement",
    )

    assert result["status"] == "High Review Priority"
    assert result["trust_score"] == 90
    assert result["review_required"] is True
    assert len(result["findings"]) == 3


def test_invalid_invoice():
    """Non-numeric quantity should return Invalid Data."""

    result = check_invoice(
        quantity="invalid",
        unit_price=100,
        market_price=100,
        budget=1500,
        claimed_total=1000,
        invoice_id="INV003",
    )

    assert result["status"] == "Invalid Data"
    assert result["review_required"] is True
    assert len(result["findings"]) > 0


def test_negative_quantity():
    """Negative quantity should be rejected."""

    result = check_invoice(
        quantity=-5,
        unit_price=100,
        market_price=100,
        budget=1500,
        claimed_total=1000,
    )

    assert result["status"] == "Invalid Data"
    assert result["review_required"] is True


if __name__ == "__main__":
    test_normal_invoice()
    print("PASS: Normal invoice")

    test_suspicious_invoice()
    print("PASS: Suspicious invoice")

    test_invalid_invoice()
    print("PASS: Invalid invoice")

    test_negative_quantity()
    print("PASS: Negative quantity")

    print("\nAll TrustCheck tests passed!")
