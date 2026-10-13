import re
import pymupdf as fitz
from typing import Dict, Any, List, Optional
from decimal import Decimal

CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "CAD": "CAD",
    "AUD": "AUD",
    "USD": "USD",
    "EUR": "EUR",
    "GBP": "GBP"
}

class PDFInvoiceParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extracts metadata and structured line items from selectable text PDF invoices.
        Supports both single-line tabular rows and multi-line column block flows.
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        warnings = []
        full_text = ""
        total_text_chars = 0
        pages_text = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text("text")
            pages_text.append((page_idx + 1, text))
            total_text_chars += len(text.strip())
            full_text += f"\n--- Page {page_idx + 1} ---\n" + text

        # Check for scanned PDF with no selectable text
        if total_text_chars < 40:
            return {
                "parse_status": "failed",
                "warnings": ["OCR not supported in this MVP. Document contains no selectable text."],
                "raw_text": "",
                "supplier_name": None,
                "invoice_number": None,
                "invoice_date": None,
                "currency": "USD",
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "freight_amount": 0.0,
                "total_amount": 0.0,
                "lines": []
            }

        # 1. Detect Currency
        currency = "USD"
        for sym, code in CURRENCY_SYMBOLS.items():
            if sym in full_text:
                currency = code
                break

        # 2. Detect Invoice Number
        inv_match = re.search(r"(?:Invoice\s*(?:#|No|Number|ID)?[:\s]+)([A-Za-z0-9\-_/]+)", full_text, re.IGNORECASE)
        invoice_number = inv_match.group(1).strip() if inv_match else f"INV-{filename.split('.')[0]}"

        # 3. Detect Supplier Name
        supplier_name = "Supplier"
        first_page_lines = [l.strip() for l in pages_text[0][1].split("\n") if l.strip()]
        for line in first_page_lines[:6]:
            if not any(k in line.lower() for k in ["invoice", "date", "bill to", "ship to", "page", "tax", "total", "po", "commercial"]):
                if len(line) > 2 and len(line) < 60:
                    supplier_name = line
                    break

        # 4. Detect Date
        date_match = re.search(r"(?:Date|Dated)[:\s]+([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4})", full_text, re.IGNORECASE)
        invoice_date = date_match.group(1).strip() if date_match else None

        # 5. Extract Line Items
        lines = []
        line_num = 1

        # Heuristic Pattern A: Sequential multi-line table blocks (Common in PyMuPDF)
        # Line 0: Description or SKU + Description
        # Line 1: Quantity (e.g. 100)
        # Line 2: Unit (e.g. each, box)
        # Line 3: Unit Price (e.g. $13.20)
        # Line 4: Line Total (e.g. $1,320.00)
        for page_idx, page_content in pages_text:
            text_lines = [l.strip() for l in page_content.split("\n") if l.strip()]
            i = 0
            while i < len(text_lines):
                cur = text_lines[i]
                # Skip header rows
                if any(h in cur.lower() for h in ["description", "unit price", "subtotal", "total amount", "balance due", "page "]):
                    i += 1
                    continue

                # Check if next 4 lines match qty, unit, price, total
                if i + 4 < len(text_lines):
                    q_str = text_lines[i+1]
                    u_str = text_lines[i+2]
                    p_str = text_lines[i+3]
                    t_str = text_lines[i+4]

                    # Verify patterns:
                    # q_str is a number
                    # u_str is a unit word
                    # p_str has a price format ($13.20 or 13.20)
                    # t_str has a total format ($1,320.00)
                    is_qty = bool(re.match(r"^\d+(?:\.\d+)?$", q_str))
                    is_unit = bool(re.match(r"^(ea|each|box|pk|pack|pcs|unit|dz|bundle|roll|tin|case|carton)$", u_str, re.IGNORECASE))
                    is_price = bool(re.search(r"[\$€£]?\s*\d+\.\d{2}", p_str))
                    is_total = bool(re.search(r"[\$€£]?\s*[\d,]+\.\d{2}", t_str))

                    if is_qty and (is_unit or is_price) and is_total:
                        qty = float(q_str)
                        clean_price = float(re.sub(r"[^\d.]", "", p_str))
                        clean_total = float(re.sub(r"[^\d.]", "", t_str))

                        # Extract SKU if cur begins with SKU-like token
                        sku = None
                        desc = cur
                        sku_match = re.match(r"^([A-Za-z0-9\-_]{3,20})\s+(.+)$", cur)
                        if sku_match:
                            sku = sku_match.group(1)
                            desc = sku_match.group(2).strip()

                        snippet = f"{cur}   {q_str} {u_str}   {p_str}   {t_str}"
                        lines.append({
                            "line_number": line_num,
                            "sku": sku,
                            "description": desc,
                            "quantity": qty,
                            "unit": u_str.lower() if is_unit else "each",
                            "unit_price": clean_price,
                            "discount": 0.0,
                            "tax_rate": 0.0,
                            "total_price": clean_total,
                            "source_page": page_idx,
                            "source_text": snippet
                        })
                        line_num += 1
                        i += 5
                        continue

                # Pattern B: Single line horizontal row
                # e.g. "SKU-HUB-07  Type C Dock 7P Aluminum  100  each  $13.20  $1,320.00"
                row_match = re.match(
                    r"^(?:([A-Za-z0-9\-_]{3,20})\s+)?([A-Za-z0-9\s,\-\./()#+&]+?)\s+(\d+(?:\.\d+)?)\s+(ea|each|box|pk|pack|pcs|unit|dz)?\s*[\$€£]?\s*(\d+(?:\.\d{1,2})?)\s+[\$€£]?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)$",
                    cur,
                    re.IGNORECASE
                )
                if row_match and not any(h in cur.lower() for h in ["description", "price", "subtotal", "total"]):
                    sku = row_match.group(1)
                    desc = row_match.group(2).strip()
                    qty = float(row_match.group(3))
                    unit = row_match.group(4) or "each"
                    price = float(row_match.group(5))
                    tot = float(row_match.group(6).replace(",", ""))

                    lines.append({
                        "line_number": line_num,
                        "sku": sku,
                        "description": desc,
                        "quantity": qty,
                        "unit": unit.lower(),
                        "unit_price": price,
                        "discount": 0.0,
                        "tax_rate": 0.0,
                        "total_price": tot,
                        "source_page": page_idx,
                        "source_text": cur
                    })
                    line_num += 1

                i += 1

        # Calculate or extract total amount
        total_match = re.search(r"(?:Total Amount|Total|Balance Due)[:\s]+[\$€£]?\s*([0-9,]+\.[0-9]{2})", full_text, re.IGNORECASE)
        if total_match:
            total_amount = float(total_match.group(1).replace(",", ""))
        else:
            total_amount = sum(item["total_price"] for item in lines) if lines else 0.0

        if not lines:
            warnings.append("No line items could be automatically extracted. Please verify invoice layout.")

        return {
            "parse_status": "completed" if lines else "warning",
            "warnings": warnings,
            "raw_text": full_text,
            "supplier_name": supplier_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "currency": currency,
            "subtotal": round(sum(l["total_price"] for l in lines), 2) if lines else total_amount,
            "tax_amount": 0.0,
            "freight_amount": 0.0,
            "total_amount": round(total_amount, 2),
            "lines": lines
        }
