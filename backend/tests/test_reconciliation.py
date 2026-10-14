import pytest
from decimal import Decimal
from backend.app.engine.reconciliation import ReconciliationEngine, to_dec


def test_invalid_numeric_value_is_rejected():
    with pytest.raises(ValueError, match="Invalid numeric value"):
        ReconciliationEngine.reconcile([
            {"description": "Bad line", "quantity": "not-a-number", "unit_price": 10}
        ])


def test_non_finite_numeric_values_are_rejected():
    for non_finite in [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValueError, match="Non-finite"):
            to_dec(non_finite)

        with pytest.raises(ValueError, match="Non-finite"):
            ReconciliationEngine.reconcile([
                {"description": "Inf line", "quantity": non_finite, "unit_price": 10}
            ])


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
    assert res["amount_at_risk"] == 120.00
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

    # When unconfirmed: finding is info, finding amount is 0.0, and headline amount_at_risk is 0.0
    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="USD"
    )

    assert res["findings_count"] == 1
    finding = res["findings"][0]
    assert finding["type"] == "QUANTITY_MISMATCH"
    assert finding["amount_at_risk"] == 0.0
    assert res["amount_at_risk"] == 0.0
    assert res["unconfirmed_amount_at_risk"] == 200.00
    assert finding["severity"] == "info"

    # When confirmed: finding is warning and headline amount_at_risk includes extra_cost
    confirmed = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        options={"quantity_check_confirmed": True},
    )
    # (120 - 100) * $10.00 = $200.00 when fulfillment is confirmed.
    assert confirmed["findings"][0]["amount_at_risk"] == 200.00
    assert confirmed["amount_at_risk"] == 200.00


def test_overlapping_findings_do_not_double_count_exposure():
    """
    Ensures that when an invoice line has both a PO PRICE_MISMATCH and a HISTORICAL_PRICE_ANOMALY,
    the price variance is not counted twice. The primary exposure is assigned to PRICE_MISMATCH,
    and HISTORICAL_PRICE_ANOMALY is marked as supporting context with 0.0 exposure.
    """
    invoice_lines = [
        {
            "id": "inv-overlap-1",
            "line_number": 1,
            "sku": "SKU-HUB-07",
            "description": "USB-C Hub, 7-in-1",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 13.20,
            "total_price": 1320.00,
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
    historical_prices = {
        "usb-c hub, 7-in-1": {
            "median_price": 10.00,
            "count": 5
        }
    }

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        historical_prices=historical_prices,
        currency="USD",
        options={"historical_price_check": True, "historical_alert_percent": 5.0}
    )

    types = [f["type"] for f in res["findings"]]
    assert "PRICE_MISMATCH" in types
    assert "HISTORICAL_PRICE_ANOMALY" in types

    price_mismatch = next(f for f in res["findings"] if f["type"] == "PRICE_MISMATCH")
    hist_anomaly = next(f for f in res["findings"] if f["type"] == "HISTORICAL_PRICE_ANOMALY")

    assert price_mismatch["amount_at_risk"] == 120.00
    assert price_mismatch["evidence_json"]["is_primary_exposure"] is True

    # Corroborating historical anomaly has zero monetary exposure to avoid double-counting
    assert hist_anomaly["amount_at_risk"] == 0.0
    assert hist_anomaly["evidence_json"]["is_primary_exposure"] is False
    assert hist_anomaly["evidence_json"]["primary_finding_type"] == "PRICE_MISMATCH"

    # Headline amount_at_risk strictly matches sum of finding amounts at risk
    sum_findings = sum(f["amount_at_risk"] for f in res["findings"])
    assert res["amount_at_risk"] == 120.00
    assert sum_findings == res["amount_at_risk"]


def test_missing_total_price_derived_from_quantity_and_unit_price():
    """
    Unmatched line with missing or zero total_price should derive its monetary exposure
    from quantity * unit_price rather than understating it as 0.00.
    """
    invoice_lines = [
        {
            "id": "inv-unmatched-1",
            "line_number": 1,
            "sku": "SKU-SPECIAL-99",
            "description": "Custom Calibration Tool",
            "quantity": 4.0,
            "unit": "each",
            "unit_price": 250.00,
            "total_price": None  # Missing total_price
        }
    ]
    po_lines = [
        {
            "id": "po-1",
            "line_number": 1,
            "sku": "SKU-OTHER",
            "description": "Completely Different Item",
            "quantity": 10.0,
            "unit": "each",
            "unit_price": 10.00,
            "total_price": 100.00
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="USD"
    )

    unmatched = next(f for f in res["findings"] if f["type"] == "UNMATCHED_LINE")
    # Derived from 4 * 250.00 = 1000.00
    assert unmatched["amount_at_risk"] == 1000.00


def test_currency_incompatibility_blocks_raw_arithmetic():
    """
    Price comparisons should not proceed when invoice and PO currencies do not match.
    """
    invoice_lines = [
        {
            "id": "inv-eur",
            "line_number": 1,
            "sku": "SKU-HUB-07",
            "description": "USB-C Hub, 7-in-1",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 13.20,
            "total_price": 1320.00
        }
    ]
    po_lines = [
        {
            "id": "po-usd",
            "line_number": 1,
            "sku": "SKU-HUB-07",
            "description": "USB-C Hub, 7-in-1",
            "quantity": 100.0,
            "unit": "each",
            "unit_price": 12.00,
            "total_price": 1200.00,
            "currency": "USD"
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="EUR"
    )

    types = [f["type"] for f in res["findings"]]
    assert "CURRENCY_MISMATCH" in types
    assert "PRICE_MISMATCH" not in types  # Raw price mismatch is blocked


def test_partial_shipment_with_remaining_quantity():
    """
    Evaluates quantity discrepancy against remaining_quantity instead of full original PO quantity.
    """
    invoice_lines = [
        {
            "id": "inv-partial",
            "line_number": 1,
            "sku": "SKU-CAB-02",
            "description": "Braided Type-C Cable",
            "quantity": 50.0,
            "unit": "each",
            "unit_price": 10.00,
            "total_price": 500.00
        }
    ]
    po_lines = [
        {
            "id": "po-1",
            "line_number": 1,
            "sku": "SKU-CAB-02",
            "description": "Braided Type-C Cable",
            "quantity": 100.0,
            "remaining_quantity": 40.0,  # 60 units already fulfilled on prior shipment
            "unit": "each",
            "unit_price": 10.00,
            "total_price": 1000.00
        }
    ]

    res = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines,
        currency="USD",
        options={"quantity_check_confirmed": True}
    )

    qty_finding = next(f for f in res["findings"] if f["type"] == "QUANTITY_MISMATCH")
    # (50 billed - 40 remaining) * $10.00 = $100.00 extra cost
    assert qty_finding["amount_at_risk"] == 100.00
    assert qty_finding["evidence_json"]["extra_quantity"] == 10.0


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
