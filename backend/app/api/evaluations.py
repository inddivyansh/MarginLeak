import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.auth import get_current_user, get_user_workspace
from backend.app.database import get_db
from backend.app.models import ModelEvaluation, Workspace, Document, Invoice, InvoiceLine, PurchaseOrder, PurchaseOrderLine, Reconciliation, LineMatch, Finding, User
from backend.app.ai.tinker_client import tinker_client
from backend.app.ai.fallback_engine import FallbackNormalizer
from backend.app.engine.reconciliation import ReconciliationEngine

router = APIRouter(tags=["Evaluations & Demo"])

class NormalizeTestRequest(BaseModel):
    description: str
    sku: str = ""

@router.get("/evaluations/latest")
def get_latest_evaluation(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Returns the benchmark comparison between Baseline A, Base Model, and Tinker Fine-Tuned Model."""
    # Check DB first
    eval_record = db.query(ModelEvaluation).order_by(ModelEvaluation.created_at.desc()).first()
    if eval_record:
        return {
            "model_name": eval_record.model_name,
            "dataset_version": eval_record.dataset_version,
            "config": eval_record.config_json,
            "metrics": eval_record.metrics_json,
            "sample_comparisons": eval_record.sample_outputs_json,
            "created_at": eval_record.created_at
        }

    # Load from default pre-evaluated benchmark artifact
    artifact_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tinker_experiment", "benchmark_results.json")
    if os.path.exists(artifact_path):
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data

    # Do not fabricate performance numbers when no benchmark artifact exists.
    return {
        "model_name": "No benchmark artifact available",
        "dataset_version": None,
        "config": {},
        "metrics": {},
        "improvements": None,
        "sample_comparisons": [],
        "status": "not_run",
    }


@router.post("/evaluations/normalize-test")
def test_normalize_description(req: NormalizeTestRequest, user: User = Depends(get_current_user)):
    """Interactive endpoint to test line-item normalization live in the web UI."""
    return tinker_client.normalize_line(req.description, req.sku or None)


@router.post("/demo/seed-sample-scenario")
def seed_sample_scenario(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    One-click setup for live demo on Render:
    Creates a realistic small e-commerce retailer scenario with 1 Purchase Order and 1 Supplier Invoice
    containing intentional price increases, quantity overcharges, and historical price spikes.
    """
    ws = get_user_workspace(user, db)

    # 1. Create Purchase Order
    po_doc = Document(
        workspace_id=ws.id,
        type="purchase_order",
        filename="PO_2026_1042_ShenzhenApex.csv",
        sha256="abc123samplepo" + str(uuid.uuid4())[:8],
        supplier_name="Shenzhen Apex Electronics Co.",
        supplier_key="shenzhen_apex_electronics_co",
        document_number="PO-1042",
        currency="USD",
        parse_status="completed",
        parse_warnings=[]
    )
    db.add(po_doc)
    db.commit()

    po = PurchaseOrder(
        workspace_id=ws.id,
        document_id=po_doc.id,
        po_number="PO-1042",
        supplier_name="Shenzhen Apex Electronics Co.",
        supplier_key="shenzhen_apex_electronics_co",
        currency="USD",
        status="open"
    )
    db.add(po)
    db.commit()

    po_items = [
        ("SKU-HUB-07", "USB-C Hub, 7-in-1 Aluminum Dock", 100.0, "each", 12.00),
        ("SKU-CAB-02", "Braided USB-C to Lightning Cable 2M Black", 200.0, "each", 3.50),
        ("SKU-CHG-65", "65W GaN Fast Wall Charger Dual Port", 100.0, "each", 14.50),
        ("SKU-MNT-MAG", "Magnetic Car Phone Mount with Qi Wireless", 50.0, "each", 8.00),
        ("SKU-EAR-PRO", "True Wireless Earbuds with ANC Case", 80.0, "each", 22.00)
    ]

    po_lines = []
    for idx, (sku, desc, qty, unit, price) in enumerate(po_items):
        pl = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=idx + 1,
            sku=sku,
            description=desc,
            quantity=qty,
            unit=unit,
            unit_price=price,
            total_price=qty * price
        )
        db.add(pl)
        po_lines.append(pl)
    db.commit()

    # 2. Create Historical Invoices (to establish price memory)
    for past_idx in range(1, 4):
        hist_inv = Invoice(
            workspace_id=ws.id,
            invoice_number=f"INV-HIST-2026-0{past_idx}",
            supplier_name="Shenzhen Apex Electronics Co.",
            supplier_key="shenzhen_apex_electronics_co",
            invoice_date=f"2026-0{past_idx}-15",
            currency="USD",
            total_amount=3850.00
        )
        db.add(hist_inv)
        db.commit()
        for idx, (sku, desc, qty, unit, price) in enumerate(po_items):
            db.add(InvoiceLine(
                invoice_id=hist_inv.id,
                line_number=idx + 1,
                sku=sku,
                description=desc,
                quantity=qty,
                unit=unit,
                unit_price=price,
                total_price=qty * price,
                source_page=1,
                source_text=f"{desc}   {qty} ea   ${price:.2f}"
            ))
    db.commit()

    # 3. Create Current Invoice with realistic intentional discrepancies
    inv_doc = Document(
        workspace_id=ws.id,
        type="invoice",
        filename="INV_APEX_2026_8891.pdf",
        sha256="xyz789sampleinv" + str(uuid.uuid4())[:8],
        supplier_name="Shenzhen Apex Electronics Co.",
        supplier_key="shenzhen_apex_electronics_co",
        document_number="INV-8891",
        document_date="2026-10-12",
        currency="USD",
        parse_status="completed",
        parse_warnings=[]
    )
    db.add(inv_doc)
    db.commit()

    inv = Invoice(
        workspace_id=ws.id,
        document_id=inv_doc.id,
        invoice_number="INV-8891",
        supplier_name="Shenzhen Apex Electronics Co.",
        supplier_key="shenzhen_apex_electronics_co",
        invoice_date="2026-10-12",
        currency="USD",
        total_amount=4860.00
    )
    db.add(inv)
    db.commit()

    # Invoice lines containing the intentional discrepancies:
    # Line 1: Type C Dock 7P (PO has USB-C Hub 7-in-1 @ $12.00) -> Billed at $13.20 ($120 discrepancy)
    # Line 2: Braided Type C to Lightning Cable -> Billed 240 units vs 200 PO (40 unapproved extra units @ $3.50 = $140 discrepancy)
    # Line 3: 65W GaN Dual Port Fast Charger -> Billed at $14.50 (Exact match)
    # Line 4: Magnetic Wireless Qi Car Mount -> Billed at $9.60 (Historical anomaly: was $8.00 across 3 past invoices, +20%)
    # Line 5: Duplicate of Line 3 accidentally repeated at end of invoice
    curr_items = [
        ("SKU-HUB-07", "Type C Dock 7P Aluminum (USB-C 7-in-1)", 100.0, "each", 13.20, "Page 1: Type C Dock 7P Aluminum   100 ea   $13.20   $1,320.00"),
        ("SKU-CAB-02", "Braided Type-C to Lightning 2M Black", 240.0, "each", 3.50, "Page 1: Braided Type-C to Lightning 2M   240 ea   $3.50   $840.00"),
        ("SKU-CHG-65", "65W GaN Wall Charger Dual USB", 100.0, "each", 14.50, "Page 1: 65W GaN Wall Charger Dual USB   100 ea   $14.50   $1,450.00"),
        ("SKU-MNT-MAG", "Mag Car Phone Qi Wireless Mount", 50.0, "each", 9.60, "Page 2: Mag Car Phone Qi Wireless Mount   50 ea   $9.60   $480.00"),
        ("SKU-CHG-65", "65W GaN Wall Charger Dual USB", 100.0, "each", 14.50, "Page 2: 65W GaN Wall Charger Dual USB (DUPLICATE)   100 ea   $14.50   $1,450.00")
    ]

    for idx, (sku, desc, qty, unit, price, snippet) in enumerate(curr_items):
        db.add(InvoiceLine(
            invoice_id=inv.id,
            line_number=idx + 1,
            sku=sku,
            description=desc,
            quantity=qty,
            unit=unit,
            unit_price=price,
            total_price=qty * price,
            source_page=1 if idx < 3 else 2,
            source_text=snippet
        ))
    db.commit()

    # 4. Automatically trigger reconciliation run
    req = {
        "workspace_id": ws.id,
        "invoice_id": inv.id,
        "purchase_order_id": po.id,
        "options": {
            "historical_price_check": True,
            "price_tolerance_percent": 2.0,
            "historical_alert_percent": 5.0,
            "use_model_normalization": True,
            "quantity_check_confirmed": True
        }
    }
    from backend.app.api.reconciliations import create_reconciliation
    from backend.app.schemas import ReconciliationCreateRequest
    recon_res = create_reconciliation(ReconciliationCreateRequest(**req), db, user=user)

    return {
        "status": "success",
        "message": "Realistic e-commerce supplier scenario seeded successfully!",
        "workspace_id": ws.id,
        "invoice_id": inv.id,
        "purchase_order_id": po.id,
        "reconciliation_id": recon_res.id,
        "findings_count": recon_res.findings_count,
        "amount_at_risk": recon_res.amount_at_risk
    }
