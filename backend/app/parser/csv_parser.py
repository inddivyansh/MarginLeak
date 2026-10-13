import io
import re
import pandas as pd
from typing import Dict, Any, List, Optional
from decimal import Decimal

COLUMN_ALIASES = {
    "sku": ["sku", "item_code", "product_code", "part_no", "part_number", "item_id", "code"],
    "description": ["description", "item", "product", "product_name", "item_description", "title", "name"],
    "quantity": ["quantity", "qty", "count", "ordered_qty", "qty_ordered", "units"],
    "unit": ["unit", "uom", "unit_of_measure", "pack", "package"],
    "unit_price": ["unit_price", "price", "unit_cost", "cost", "rate", "agreed_price", "po_price"],
    "total_price": ["total", "total_price", "amount", "line_total", "extended_price"],
    "po_number": ["po_number", "po_no", "order_no", "purchase_order", "po"]
}

def clean_currency_val(val: Any) -> float:
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    val_str = re.sub(r"[^\d.-]", "", val_str)
    try:
        return float(val_str)
    except Exception:
        return 0.0

class PurchaseOrderFileParser:
    @staticmethod
    def detect_columns(df_columns: List[str]) -> Dict[str, str]:
        """Auto-detects semantic field mappings from CSV/Excel column names"""
        mapping = {}
        cols_lower = {str(c).strip().lower(): c for c in df_columns}

        for canonical, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in cols_lower:
                    mapping[canonical] = cols_lower[alias]
                    break

        return mapping

    @staticmethod
    def parse_file(
        file_bytes: bytes,
        filename: str,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Parses CSV or Excel purchase order into structured lines.
        """
        warnings = []
        is_excel = filename.lower().endswith((".xlsx", ".xls"))

        try:
            if is_excel:
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                # Try UTF-8 then ISO-8859-1
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
        except Exception as e:
            return {
                "parse_status": "failed",
                "warnings": [f"Could not read spreadsheet file: {str(e)}"],
                "lines": [],
                "detected_columns": {}
            }

        detected = PurchaseOrderFileParser.detect_columns(list(df.columns))
        active_mapping = custom_mapping or detected

        if "description" not in active_mapping and "sku" not in active_mapping:
            return {
                "parse_status": "failed",
                "warnings": ["Spreadsheet must contain at least a 'description' or 'sku' column."],
                "lines": [],
                "detected_columns": detected
            }

        desc_col = active_mapping.get("description")
        sku_col = active_mapping.get("sku")
        qty_col = active_mapping.get("quantity")
        price_col = active_mapping.get("unit_price")
        unit_col = active_mapping.get("unit")
        po_col = active_mapping.get("po_number")

        lines = []
        po_numbers_found = set()

        for idx, row in df.iterrows():
            desc_val = str(row[desc_col]).strip() if desc_col and pd.notna(row.get(desc_col)) else None
            sku_val = str(row[sku_col]).strip() if sku_col and pd.notna(row.get(sku_col)) else None

            if not desc_val and not sku_val:
                continue

            desc = desc_val or sku_val
            qty = clean_currency_val(row.get(qty_col)) if qty_col else 1.0
            price = clean_currency_val(row.get(price_col)) if price_col else 0.0
            unit = str(row[unit_col]).strip().lower() if unit_col and pd.notna(row.get(unit_col)) else "each"

            if po_col and pd.notna(row.get(po_col)):
                po_numbers_found.add(str(row[po_col]).strip())

            lines.append({
                "line_number": idx + 1,
                "sku": sku_val,
                "description": desc,
                "quantity": max(qty, 0.0),
                "unit": unit or "each",
                "unit_price": max(price, 0.0),
                "discount": 0.0,
                "tax_rate": 0.0,
                "total_price": round(qty * price, 2)
            })

        default_po_num = list(po_numbers_found)[0] if po_numbers_found else f"PO-{filename.split('.')[0]}"

        if not lines:
            warnings.append("No valid data rows found in spreadsheet.")

        return {
            "parse_status": "completed" if lines else "warning",
            "warnings": warnings,
            "po_number": default_po_num,
            "detected_columns": detected,
            "lines": lines
        }
