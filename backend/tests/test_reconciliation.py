from decimal import Decimal
from backend.app.engine.reconciliation import ReconciliationEngine


def test_invalid_numeric_value_is_rejected():
    try:
        ReconciliationEngine.reconcile([
            {"description": "Bad line", "quantity": "not-a-number", "unit_price": 10}
        ])
    except ValueError as exc:
        assert "Invalid numeric value" in str(exc)
    else:
        raise AssertionError("Malformed numeric input must be rejected")

def test_price_mismatch_rule():
    invoice_lines = [
        {
            "id": "inv-1",
            "line_number": 1,
            "sku": "SKU-HUB-07",
            "description": "USB-C Hub, 7-in-1",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 13.20,
            "total_price": 1320.00,
            "source_page": 1,
            "source_text": "USB-C Hub, 7-in-1   100 ea   $13.20   $1,320.00"
        }
    ]
    po_lines = [
        {
            "id": "po-1",
            "line_number": 1,
            "sku": "SKU-HUB-07",
            "description": "USB-C Hub, 7-in-1",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 12.00,
            "total_price": 1200.00
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="USD"
    )

    assert res["findings_count"] == 1
    finding = res["findings"][0]
    assert finding["type"] == "PRICE_MISMATCH"
    # ($13.20 - $12.00) * 100 = $120.00
    assert finding["amount_at_risk"] == 120.00
    assert "excess cost: usd 120.00" in finding["explanation"].lower() or "120.00" in finding["explanation"]

def test_quantity_mismatch_rule():
    invoice_lines = [
        {
            "id": "inv-2",
            "line_number": 1,
            "sku": "SKU-CAB-02",
            "description": "Braided Type-C Cable",
            "quantity": 120.0,
            "unit": "each",
            "unit_price": 10.00,
            "total_price": 1200.00,
            "source_page": 1,
            "source_text": "Braided Type-C Cable   120 ea   $10.00"
        }
    ]
    po_lines = [
        {
            "id": "po-2",
            "line_number": 1,
            "sku": "SKU-CAB-02",
            "description": "Braided Type-C Cable",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 10.00,
            "total_price": 1000.00
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="USD"
    )

    assert res["findings_count"] == 1
    finding = res["findings"][0]
    assert finding["type"] == "QUANTITY_MISMATCH"
    assert finding["amount_at_risk"] == 0.0
    assert finding["severity"] == "info"

    confirmed = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        options={"quantity_check_confirmed": True},
    )
    # (120 - 100) * $10.00 = $200.00 when fulfillment is confirmed.
    assert confirmed["findings"][0]["amount_at_risk"] == 200.00

def test_duplicate_line_rule():
    invoice_lines = [
        {
            "id": "inv-3a",
            "line_number": 1,
            "sku": "SKU-TEST",
            "description": "Wireless Mouse",
            "quantity": 50.0,
            "unit": "each",
            "unit_price": 15.00,
            "total_price": 750.00
        },
        {
            "id": "inv-3b",
            "line_number": 2,
            "sku": "SKU-TEST",
            "description": "Wireless Mouse",
            "quantity": 50.0,
            "unit": "each",
            "unit_price": 15.00,
            "total_price": 750.00
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=[],
        currency="USD"
    )

    dup_findings = [f for f in res["findings"] if f["type"] == "DUPLICATE_CANDIDATE"]
    assert len(dup_findings) == 1
    assert dup_findings[0]["amount_at_risk"] == 750.00
