import statistics
from typing import List, Optional, Dict, Any
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Invoice, InvoiceLine, Workspace
from backend.app.schemas import HistoricalPriceItem

router = APIRouter(tags=["Price History"])

@router.get("/history/prices", response_model=List[HistoricalPriceItem])
def get_price_history(workspace_id: str, supplier_key: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(InvoiceLine, Invoice).join(Invoice, InvoiceLine.invoice_id == Invoice.id)

    query = query.filter(Invoice.workspace_id == workspace_id)
    if supplier_key:
        query = query.filter(Invoice.supplier_key == supplier_key)

    records = query.order_by(Invoice.invoice_date.desc(), InvoiceLine.line_number.asc()).all()

    # Group by (supplier_key, normalized_item, currency, unit)
    grouped = defaultdict(list)
    for line, inv in records:
        item_norm = line.description.strip().lower()
        key = (inv.supplier_key or "unknown", item_norm, inv.currency, line.unit or "each")
        grouped[key].append({
            "price": float(line.unit_price),
            "date": inv.invoice_date or inv.created_at.strftime("%Y-%m-%d"),
            "invoice_number": inv.invoice_number,
            "quantity": float(line.quantity)
        })

    results = []
    for (supp, item_desc, curr, unit), items in grouped.items():
        prices = [x["price"] for x in items]
        med_price = round(statistics.median(prices), 2)
        min_p = round(min(prices), 2)
        max_p = round(max(prices), 2)
        latest_p = prices[0]

        results.append(HistoricalPriceItem(
            supplier_key=supp,
            item_normalized=item_desc,
            currency=curr,
            unit=unit,
            purchase_count=len(items),
            median_unit_price=med_price,
            min_unit_price=min_p,
            max_unit_price=max_p,
            latest_unit_price=latest_p,
            latest_purchase_date=items[0]["date"],
            price_history=items
        ))

    return sorted(results, key=lambda x: x.purchase_count, reverse=True)
