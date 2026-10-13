import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from backend.app.engine.matcher import LineMatcher

def to_dec(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (ArithmeticError, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value: {val!r}") from exc

class ReconciliationEngine:
    @staticmethod
    def reconcile(
        invoice_lines: List[Dict[str, Any]],
        po_lines: Optional[List[Dict[str, Any]]] = None,
        historical_prices: Optional[Dict[str, Dict[str, Any]]] = None,
        existing_invoice_numbers: Optional[List[str]] = None,
        invoice_number: Optional[str] = None,
        supplier_key: Optional[str] = None,
        currency: str = "USD",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes deterministic accounts payable audit rules on invoice line items against
        purchase orders and historical supplier prices.
        """
        opts = options or {}
        price_tol_pct = Decimal(str(opts.get("price_tolerance_percent", 2.0)))
        hist_alert_pct = Decimal(str(opts.get("historical_alert_percent", 5.0)))
        check_history = opts.get("historical_price_check", True)
        use_model = opts.get("use_model_normalization", True)
        quantity_check_confirmed = opts.get("quantity_check_confirmed", False)

        findings = []
        matches = []
        total_amount_at_risk = Decimal("0.00")

        # 1. Check for Duplicate Invoice Submission
        if existing_invoice_numbers and invoice_number and invoice_number in existing_invoice_numbers:
            findings.append({
                "id": str(uuid.uuid4()),
                "invoice_line_id": None,
                "po_line_id": None,
                "type": "DUPLICATE_CANDIDATE",
                "severity": "critical",
                "amount_at_risk": 0.0,
                "currency": currency,
                "explanation": f"Duplicate Invoice Warning: Invoice number '{invoice_number}' was previously uploaded and processed for supplier '{supplier_key or 'Unknown'}'.",
                "evidence_json": {
                    "reason": "duplicate_invoice_number",
                    "duplicate_invoice_number": invoice_number,
                    "supplier_key": supplier_key
                },
                "status": "open"
            })

        # 2. Check for Duplicate Lines within this invoice
        seen_lines = {}
        duplicate_line_ids = set()
        for idx, inv in enumerate(invoice_lines):
            key = (
                inv.get("description", "").strip().lower(),
                to_dec(inv.get("quantity")),
                to_dec(inv.get("unit_price")),
            )
            if key in seen_lines:
                prev_line = seen_lines[key]
                duplicate_line_ids.add(inv.get("id"))
                dup_amount = to_dec(inv.get("total_price") or (to_dec(inv.get("quantity")) * to_dec(inv.get("unit_price"))))
                total_amount_at_risk += dup_amount
                findings.append({
                    "id": str(uuid.uuid4()),
                    "invoice_line_id": inv.get("id"),
                    "po_line_id": None,
                    "type": "DUPLICATE_CANDIDATE",
                    "severity": "critical",
                    "amount_at_risk": float(dup_amount),
                    "currency": currency,
                    "explanation": f"Duplicate Line Warning: Line {inv.get('line_number')} appears identical to Line {prev_line.get('line_number')} ('{inv.get('description')}' for {inv.get('quantity')} {inv.get('unit')} @ {currency} {inv.get('unit_price')}).",
                    "evidence_json": {
                        "duplicate_of_line": prev_line.get("line_number"),
                        "current_line": inv.get("line_number"),
                        "description": inv.get("description"),
                        "quantity": float(inv.get("quantity", 0)),
                        "unit_price": float(inv.get("unit_price", 0)),
                        "calculation_formula": f"{inv.get('quantity')} × {inv.get('unit_price')} = {dup_amount}"
                    },
                    "status": "open"
                })
            else:
                seen_lines[key] = inv

        # 3. Match Invoice Lines to Purchase Order Lines (if PO provided)
        matched_results = []
        if po_lines:
            matched_results = LineMatcher.match_invoice_lines(
                invoice_lines=invoice_lines,
                po_lines=po_lines,
                use_model_normalization=use_model
            )

        matched_count = 0
        ambiguous_count = 0
        unmatched_count = 0

        for match_info in matched_results:
            inv_line = match_info["invoice_line"]
            if inv_line.get("id") in duplicate_line_ids:
                continue
            po_line = match_info["matched_po_line"]
            is_ambiguous = match_info["is_ambiguous"]
            method = match_info["method"]
            confidence = match_info["confidence"]

            matches.append({
                "invoice_line_id": inv_line.get("id"),
                "po_line_id": po_line.get("id") if po_line else None,
                "method": method,
                "confidence": confidence,
                "review_status": "ambiguous" if is_ambiguous else ("matched" if po_line else "unmatched"),
                "invoice_line": inv_line,
                "po_line": po_line
            })

            if not po_line:
                unmatched_count += 1
                findings.append({
                    "id": str(uuid.uuid4()),
                    "invoice_line_id": inv_line.get("id"),
                    "po_line_id": None,
                    "type": "UNMATCHED_LINE",
                    "severity": "warning",
                    "amount_at_risk": float(to_dec(inv_line.get("total_price"))),
                    "currency": currency,
                    "explanation": f"Unmatched Item: Line {inv_line.get('line_number')} ('{inv_line.get('description')}') could not be matched to any line item in Purchase Order.",
                    "evidence_json": {
                        "invoice_line_num": inv_line.get("line_number"),
                        "invoice_desc": inv_line.get("description"),
                        "invoice_qty": float(inv_line.get("quantity", 0)),
                        "invoice_unit_price": float(inv_line.get("unit_price", 0)),
                        "invoice_snippet": inv_line.get("source_text"),
                        "invoice_page": inv_line.get("source_page", 1)
                    },
                    "status": "open"
                })
                continue

            if is_ambiguous:
                ambiguous_count += 1
                findings.append({
                    "id": str(uuid.uuid4()),
                    "invoice_line_id": inv_line.get("id"),
                    "po_line_id": po_line.get("id"),
                    "type": "AMBIGUOUS_MATCH",
                    "severity": "info",
                    "amount_at_risk": 0.0,
                    "currency": currency,
                    "explanation": f"Ambiguous Product Match: '{inv_line.get('description')}' tentatively paired with PO '{po_line.get('description')}'. {match_info.get('ambiguity_reason')}",
                    "evidence_json": {
                        "invoice_desc": inv_line.get("description"),
                        "po_desc": po_line.get("description"),
                        "match_confidence": confidence,
                        "method": method,
                        "ambiguity_reason": match_info.get("ambiguity_reason")
                    },
                    "status": "open"
                })
            else:
                matched_count += 1

            if is_ambiguous:
                continue

            # Rule 1: Unit Price Difference
            p_inv = to_dec(inv_line.get("unit_price"))
            p_po = to_dec(po_line.get("unit_price"))
            q_inv = to_dec(inv_line.get("quantity"))

            if p_po > 0:
                price_diff_per_unit = p_inv - p_po
                pct_diff = (price_diff_per_unit / p_po) * Decimal("100")

                if price_diff_per_unit > 0 and pct_diff > price_tol_pct:
                    excess_amount = (price_diff_per_unit * q_inv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    total_amount_at_risk += excess_amount

                    findings.append({
                        "id": str(uuid.uuid4()),
                        "invoice_line_id": inv_line.get("id"),
                        "po_line_id": po_line.get("id"),
                        "type": "PRICE_MISMATCH",
                        "severity": "critical" if excess_amount > Decimal("50.00") else "warning",
                        "amount_at_risk": float(excess_amount),
                        "currency": currency,
                        "explanation": f"Unit Price Increase: Invoiced at {currency} {p_inv:.2f}/unit vs authorized PO price {currency} {p_po:.2f}/unit (+{pct_diff:.1f}%). Excess cost: {currency} {excess_amount:.2f}.",
                        "evidence_json": {
                            "invoice_line_num": inv_line.get("line_number"),
                            "invoice_desc": inv_line.get("description"),
                            "invoice_unit_price": float(p_inv),
                            "invoice_qty": float(q_inv),
                            "invoice_snippet": inv_line.get("source_text"),
                            "invoice_page": inv_line.get("source_page", 1),
                            "po_line_num": po_line.get("line_number"),
                            "po_desc": po_line.get("description"),
                            "po_unit_price": float(p_po),
                            "po_qty": float(po_line.get("quantity", 0)),
                            "calculation_formula": f"({currency} {p_inv:.2f} - {currency} {p_po:.2f}) × {q_inv:.0f} units = {currency} {excess_amount:.2f}",
                            "expected_amount": float(p_po * q_inv),
                            "billed_amount": float(p_inv * q_inv),
                            "difference": float(excess_amount),
                            "percentage_difference": float(pct_diff)
                        },
                        "status": "open"
                    })

            # Rule 2: Quantity Mismatch
            q_po = to_dec(po_line.get("quantity"))
            if q_inv > q_po:
                extra_qty = q_inv - q_po
                # Excess quantity value based on agreed PO price
                extra_cost = (extra_qty * p_po).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                total_amount_at_risk += extra_cost

                findings.append({
                    "id": str(uuid.uuid4()),
                    "invoice_line_id": inv_line.get("id"),
                    "po_line_id": po_line.get("id"),
                    "type": "QUANTITY_MISMATCH",
                    "severity": "warning" if quantity_check_confirmed else "info",
                    "amount_at_risk": float(extra_cost) if quantity_check_confirmed else 0.0,
                    "currency": currency,
                    "explanation": (
                        f"Over-Quantity Invoiced: Invoiced for {q_inv:.0f} {inv_line.get('unit')} vs authorized PO quantity {q_po:.0f} (+{extra_qty:.0f} units). "
                        + (f"Value at risk: {currency} {extra_cost:.2f}." if quantity_check_confirmed else "Fulfillment status is unknown; review before treating the difference as leakage.")
                    ),
                    "evidence_json": {
                        "invoice_line_num": inv_line.get("line_number"),
                        "invoice_desc": inv_line.get("description"),
                        "invoice_qty": float(q_inv),
                        "invoice_unit_price": float(p_inv),
                        "invoice_snippet": inv_line.get("source_text"),
                        "invoice_page": inv_line.get("source_page", 1),
                        "po_line_num": po_line.get("line_number"),
                        "po_desc": po_line.get("description"),
                        "po_qty": float(q_po),
                        "po_unit_price": float(p_po),
                        "calculation_formula": f"({q_inv:.0f} - {q_po:.0f}) extra units × {currency} {p_po:.2f} = {currency} {extra_cost:.2f}",
                        "extra_quantity": float(extra_qty),
                        "difference": float(extra_cost) if quantity_check_confirmed else 0.0,
                        "quantity_review_required": not quantity_check_confirmed
                    },
                    "status": "open"
                })

            # Rule 3: Historical Price Anomaly Check
            if check_history and historical_prices:
                clean_inv_desc = inv_line.get("description", "").strip().lower()
                # Find matching historical record
                hist_match = None
                for hist_key, hist_data in historical_prices.items():
                    if hist_key in clean_inv_desc or clean_inv_desc in hist_key:
                        hist_match = hist_data
                        break

                if hist_match:
                    p_hist_median = to_dec(hist_match.get("median_price"))
                    sample_count = hist_match.get("count", 1)

                    if p_hist_median > 0:
                        hist_diff = p_inv - p_hist_median
                        hist_pct = (hist_diff / p_hist_median) * Decimal("100")

                        # If historical price rose more than historical_alert_percent and not already flagged by PO price mismatch
                        if hist_pct > hist_alert_pct:
                            hist_excess = (hist_diff * q_inv).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                            findings.append({
                                "id": str(uuid.uuid4()),
                                "invoice_line_id": inv_line.get("id"),
                                "po_line_id": po_line.get("id") if po_line else None,
                                "type": "HISTORICAL_PRICE_ANOMALY",
                                "severity": "warning",
                                "amount_at_risk": float(hist_excess),
                                "currency": currency,
                                "explanation": f"Historical Price Deviation: Current unit price {currency} {p_inv:.2f} is {hist_pct:.1f}% above historical baseline median ({currency} {p_hist_median:.2f} across {sample_count} prior orders).",
                                "evidence_json": {
                                    "current_price": float(p_inv),
                                    "historical_median": float(p_hist_median),
                                    "prior_orders_count": sample_count,
                                    "percentage_increase": float(hist_pct),
                                    "calculation_formula": f"({currency} {p_inv:.2f} - {currency} {p_hist_median:.2f}) / {currency} {p_hist_median:.2f} = +{hist_pct:.1f}%"
                                },
                                "status": "open"
                            })

        return {
            "amount_at_risk": float(total_amount_at_risk),
            "currency": currency,
            "matched_lines_count": matched_count,
            "ambiguous_lines_count": ambiguous_count,
            "unmatched_lines_count": unmatched_count,
            "findings_count": len(findings),
            "findings": findings,
            "matches": matches
        }
