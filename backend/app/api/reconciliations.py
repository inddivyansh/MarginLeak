import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import (
    Workspace, Invoice, InvoiceLine, PurchaseOrder, PurchaseOrderLine,
    Reconciliation, LineMatch, Finding, ReviewEvent, SupplierItemAlias
)
from backend.app.schemas import (
    ReconciliationCreateRequest, ReconciliationResponse,
    FindingResponse, FindingUpdate, MatchCorrectionUpdate
)
from backend.app.engine.reconciliation import ReconciliationEngine

router = APIRouter(tags=["Reconciliations"])

@router.post("/reconciliations", response_model=ReconciliationResponse)
def create_reconciliation(req: ReconciliationCreateRequest, db: Session = Depends(get_db)):
    # 1. Fetch Invoice
    invoice = db.query(Invoice).filter(Invoice.id == req.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")

    # 2. Fetch Purchase Order if specified
    po = None
    if req.purchase_order_id:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == req.purchase_order_id).first()

    # 3. Load Invoice Lines
    invoice_lines = [
        {
            "id": l.id,
            "line_number": l.line_number,
            "sku": l.sku,
            "description": l.description,
            "quantity": float(l.quantity),
            "unit": l.unit,
            "unit_price": float(l.unit_price),
            "total_price": float(l.total_price) if l.total_price else float(l.quantity * l.unit_price),
            "source_page": l.source_page,
            "source_text": l.source_text
        }
        for l in invoice.lines
    ]

    # 4. Load PO Lines
    po_lines = []
    if po:
        po_lines = [
            {
                "id": l.id,
                "line_number": l.line_number,
                "sku": l.sku,
                "description": l.description,
                "quantity": float(l.quantity),
                "unit": l.unit,
                "unit_price": float(l.unit_price),
                "total_price": float(l.total_price) if l.total_price else float(l.quantity * l.unit_price)
            }
            for l in po.lines
        ]

    # 5. Load Historical Prices for supplier
    historical_map = {}
    past_lines = (
        db.query(InvoiceLine)
        .join(Invoice)
        .filter(Invoice.workspace_id == invoice.workspace_id)
        .filter(Invoice.supplier_key == invoice.supplier_key)
        .filter(Invoice.id != invoice.id)
        .all()
    )
    from collections import defaultdict
    import statistics
    item_hist_prices = defaultdict(list)
    for pl in past_lines:
        item_hist_prices[pl.description.strip().lower()].append(float(pl.unit_price))

    for item_key, prices in item_hist_prices.items():
        if prices:
            historical_map[item_key] = {
                "median_price": statistics.median(prices),
                "count": len(prices)
            }

    # 6. Existing Invoice Numbers for duplicate detection
    existing_nums = [
        inv.invoice_number
        for inv in db.query(Invoice)
        .filter(Invoice.workspace_id == invoice.workspace_id)
        .filter(Invoice.supplier_key == invoice.supplier_key)
        .filter(Invoice.id != invoice.id)
        .all()
    ]

    # 7. Run Reconciliation Engine
    result = ReconciliationEngine.reconcile(
        invoice_lines=invoice_lines,
        po_lines=po_lines if po else None,
        historical_prices=historical_map,
        existing_invoice_numbers=existing_nums,
        invoice_number=invoice.invoice_number,
        supplier_key=invoice.supplier_key,
        currency=invoice.currency,
        options=req.options
    )

    # 8. Persist Reconciliation Record
    recon = Reconciliation(
        id=str(uuid.uuid4()),
        workspace_id=invoice.workspace_id,
        invoice_id=invoice.id,
        purchase_order_id=po.id if po else None,
        status="completed",
        amount_at_risk=result["amount_at_risk"],
        currency=result["currency"],
        matched_lines_count=result["matched_lines_count"],
        ambiguous_lines_count=result["ambiguous_lines_count"],
        unmatched_lines_count=result["unmatched_lines_count"],
        findings_count=result["findings_count"],
        options=req.options or {},
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(recon)
    db.commit()

    # 9. Persist Matches
    for m in result["matches"]:
        match_record = LineMatch(
            id=str(uuid.uuid4()),
            reconciliation_id=recon.id,
            invoice_line_id=m["invoice_line_id"],
            po_line_id=m["po_line_id"],
            method=m["method"],
            confidence=m["confidence"],
            review_status=m["review_status"]
        )
        db.add(match_record)

    # 10. Persist Findings
    for f in result["findings"]:
        finding_record = Finding(
            id=f.get("id", str(uuid.uuid4())),
            reconciliation_id=recon.id,
            invoice_line_id=f.get("invoice_line_id"),
            po_line_id=f.get("po_line_id"),
            type=f["type"],
            severity=f["severity"],
            amount_at_risk=f["amount_at_risk"],
            currency=f["currency"],
            explanation=f["explanation"],
            evidence_json=f["evidence_json"],
            status="open",
            created_at=datetime.utcnow()
        )
        db.add(finding_record)

    db.commit()
    db.refresh(recon)
    return recon


@router.get("/reconciliations", response_model=List[ReconciliationResponse])
def list_reconciliations(workspace_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Reconciliation)
    if workspace_id:
        query = query.filter(Reconciliation.workspace_id == workspace_id)
    return query.order_by(Reconciliation.created_at.desc()).all()


@router.get("/reconciliations/{id}", response_model=ReconciliationResponse)
def get_reconciliation(id: str, db: Session = Depends(get_db)):
    recon = db.query(Reconciliation).filter(Reconciliation.id == id).first()
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found.")
    return recon


@router.get("/reconciliations/{id}/findings", response_model=List[FindingResponse])
def list_findings(id: str, db: Session = Depends(get_db)):
    findings = db.query(Finding).filter(Finding.reconciliation_id == id).order_by(Finding.amount_at_risk.desc()).all()
    return findings


@router.patch("/findings/{id}", response_model=FindingResponse)
def update_finding(id: str, update: FindingUpdate, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found.")

    old_status = finding.status
    finding.status = update.status

    # Record ReviewEvent audit trail
    event = ReviewEvent(
        finding_id=finding.id,
        actor_id="reviewer",
        action=f"status_change_to_{update.status}",
        old_value_json={"status": old_status},
        new_value_json={"status": update.status},
        note=update.note,
        created_at=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(finding)
    return finding


@router.patch("/line-matches/{id}")
def correct_match(id: str, correction: MatchCorrectionUpdate, db: Session = Depends(get_db)):
    match = db.query(LineMatch).filter(LineMatch.id == id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found.")

    if correction.mark_unmatched:
        match.po_line_id = None
        match.review_status = "unmatched"
        match.method = "manual"
    elif correction.po_line_id:
        match.po_line_id = correction.po_line_id
        match.review_status = "corrected"
        match.method = "manual"

        # Save SupplierItemAlias for future automatic matching
        inv_line = db.query(InvoiceLine).filter(InvoiceLine.id == match.invoice_line_id).first()
        po_line = db.query(PurchaseOrderLine).filter(PurchaseOrderLine.id == correction.po_line_id).first()
        if inv_line and po_line:
            recon = db.query(Reconciliation).filter(Reconciliation.id == match.reconciliation_id).first()
            inv = db.query(Invoice).filter(Invoice.id == inv_line.invoice_id).first()
            if inv and recon:
                alias = SupplierItemAlias(
                    workspace_id=recon.workspace_id,
                    supplier_key=inv.supplier_key,
                    alias_normalized=inv_line.description.strip().lower(),
                    canonical_item_key=po_line.sku or po_line.description,
                    canonical_description=po_line.description,
                    unit=po_line.unit,
                    created_from="user_correction"
                )
                db.add(alias)

    db.commit()
    db.refresh(match)
    return {"status": "success", "match_id": match.id, "review_status": match.review_status}


@router.get("/reports/{reconciliation_id}.csv")
def export_csv_report(reconciliation_id: str, db: Session = Depends(get_db)):
    recon = db.query(Reconciliation).filter(Reconciliation.id == reconciliation_id).first()
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found.")

    findings = db.query(Finding).filter(Finding.reconciliation_id == reconciliation_id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Finding ID", "Status", "Type", "Severity", "Currency",
        "Amount at Risk", "Explanation", "Invoice Line", "PO Line",
        "Calculation Formula", "Source Snippet", "Page"
    ])

    for f in findings:
        ev = f.evidence_json or {}
        writer.writerow([
            f.id,
            f.status,
            f.type,
            f.severity,
            f.currency,
            f"{f.amount_at_risk:.2f}",
            f.explanation,
            ev.get("invoice_desc") or ev.get("invoice_line_num", "N/A"),
            ev.get("po_desc") or ev.get("po_line_num", "N/A"),
            ev.get("calculation_formula", ""),
            ev.get("invoice_snippet", ""),
            ev.get("invoice_page", 1)
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=MarginLeak_Exception_Report_{recon.id[:8]}.csv"}
    )
