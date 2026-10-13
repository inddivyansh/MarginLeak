from backend.app.engine.matcher import LineMatcher

def test_exact_sku_matching():
    inv_lines = [{"sku": "SKU-990", "description": "Vendor Custom Name", "unit": "each"}]
    po_lines = [{"sku": "SKU-990", "description": "Internal Canonical Name", "unit": "each"}]

    matches = LineMatcher.match_invoice_lines(inv_lines, po_lines)
    assert len(matches) == 1
    assert matches[0]["method"] == "exact_sku"
    assert matches[0]["confidence"] == 1.0
    assert matches[0]["matched_po_line"]["sku"] == "SKU-990"

def test_fuzzy_matching_with_pack_penalty():
    # Box of 100 vs Box of 200 should NOT be collapsed together
    inv_lines = [{"sku": None, "description": "Blue Nitrile Gloves 100/box", "unit": "box"}]
    po_lines = [
        {"id": "po-1", "sku": None, "description": "Blue Nitrile Gloves 200/box", "unit": "box"},
        {"id": "po-2", "sku": None, "description": "Blue Nitrile Gloves box of 100", "unit": "box"}
    ]

    matches = LineMatcher.match_invoice_lines(inv_lines, po_lines)
    assert len(matches) == 1
    # Should match po-2 (box of 100), not po-1 (box of 200)
    assert matches[0]["matched_po_line"]["id"] == "po-2"

def test_ambiguous_matching_flag():
    inv_lines = [{"sku": None, "description": "USB Cable Type C", "unit": "each"}]
    po_lines = [
        {"id": "po-a", "sku": None, "description": "USB Cable Type C 1 Meter Black", "unit": "each"},
        {"id": "po-b", "sku": None, "description": "USB Cable Type C 2 Meter Black", "unit": "each"}
    ]

    matches = LineMatcher.match_invoice_lines(inv_lines, po_lines)
    assert len(matches) == 1
    # When two options are similarly close, ambiguity flag must be true
    assert matches[0]["is_ambiguous"] is True
