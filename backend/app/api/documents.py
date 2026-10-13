import os
import hashlib
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.auth import get_authorized_workspace, get_current_user, get_user_workspace
from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models import Workspace, Document, Invoice, InvoiceLine, PurchaseOrder, PurchaseOrderLine, User
from backend.app.schemas import DocumentResponse, PurchaseOrderResponse, InvoiceResponse, ColumnMappingRequest
from backend.app.parser.pdf_parser import PDFInvoiceParser
from backend.app.parser.csv_parser import PurchaseOrderFileParser

router = APIRouter(tags=["Documents"])

@router.post("/documents/invoices", response_model=InvoiceResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only selectable text PDF invoices are supported in this MVP.")

    content = await file.read()
    if len(content) > 15 * 1024 * 1024:  # 15MB limit
        raise HTTPException(status_code=413, detail="File size exceeds 15MB limit.")

    sha256 = hashlib.sha256(content).hexdigest()

    # Get or create workspace
    ws = get_authorized_workspace(workspace_id, user, db) if workspace_id else get_user_workspace(user, db)

    # Save physical file
    file_path = os.path.join(settings.upload_dir, str(uuid.uuid4()))
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse with PyMuPDF
    parsed = PDFInvoiceParser.parse_pdf(content, file.filename)
    if parsed["parse_status"] == "failed":
        raise HTTPException(status_code=422, detail=parsed["warnings"][0])

    supplier_key = (parsed["supplier_name"] or "unknown").strip().lower().replace(" ", "_")

    doc = Document(
        workspace_id=ws.id,
        type="invoice",
        filename=file.filename,
        file_path=file_path,
        sha256=sha256,
        supplier_name=parsed["supplier_name"],
        supplier_key=supplier_key,
        document_number=parsed["invoice_number"],
        document_date=parsed["invoice_date"],
        currency=parsed["currency"],
        parse_status=parsed["parse_status"],
        parse_warnings=parsed["warnings"],
        raw_text=parsed["raw_text"]
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Create Invoice record
    inv = Invoice(
        workspace_id=ws.id,
        document_id=doc.id,
        invoice_number=parsed["invoice_number"],
        supplier_name=parsed["supplier_name"],
        supplier_key=supplier_key,
        invoice_date=parsed["invoice_date"],
        currency=parsed["currency"],
        subtotal=parsed["subtotal"],
        tax_amount=parsed["tax_amount"],
        freight_amount=parsed["freight_amount"],
        total_amount=parsed["total_amount"]
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    # Create Invoice lines
    for item in parsed["lines"]:
        line = InvoiceLine(
            invoice_id=inv.id,
            line_number=item["line_number"],
            sku=item.get("sku"),
            description=item["description"],
            quantity=item["quantity"],
            unit=item["unit"],
            unit_price=item["unit_price"],
            discount=item.get("discount", 0.0),
            tax_rate=item.get("tax_rate", 0.0),
            total_price=item.get("total_price"),
            source_page=item.get("source_page", 1),
            source_text=item.get("source_text")
        )
        db.add(line)

    db.commit()
    db.refresh(inv)
    return inv


@router.post("/purchase-orders/import")
async def preview_purchase_order(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV or Excel (.xlsx) purchase orders are supported.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Spreadsheet file exceeds 10MB limit.")

    parsed = PurchaseOrderFileParser.parse_file(content, file.filename)
    if parsed["parse_status"] == "failed":
        raise HTTPException(status_code=422, detail=parsed["warnings"][0])

    # Cache temp file for confirmation
    temp_path = os.path.join(settings.upload_dir, f"temp_{user.id}_{uuid.uuid4()}")
    with open(temp_path, "wb") as f:
        f.write(content)

    return {
        "status": "preview",
        "temp_key": os.path.basename(temp_path),
        "filename": file.filename,
        "po_number": parsed["po_number"],
        "detected_columns": parsed["detected_columns"],
        "lines_count": len(parsed["lines"]),
        "sample_lines": parsed["lines"][:5],
        "warnings": parsed["warnings"]
    }


@router.post("/purchase-orders/confirm-import", response_model=PurchaseOrderResponse)
async def confirm_purchase_order(
    req: ColumnMappingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    temp_key = os.path.basename(req.temp_key)
    temp_path = os.path.abspath(os.path.join(settings.upload_dir, temp_key))
    upload_root = os.path.abspath(settings.upload_dir)
    if not temp_key.startswith(f"temp_{user.id}_") or os.path.commonpath([temp_path, upload_root]) != upload_root:
        raise HTTPException(status_code=400, detail="Invalid upload session key.")
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Uploaded file session expired. Please re-upload.")

    with open(temp_path, "rb") as f:
        content = f.read()

    sha256 = hashlib.sha256(content).hexdigest()
    parsed = PurchaseOrderFileParser.parse_file(content, req.filename, custom_mapping=req.columns)

    ws = get_authorized_workspace(req.workspace_id, user, db)

    po_number = req.po_number or parsed["po_number"]
    supplier_name = req.supplier_name or "Standard Supplier"
    supplier_key = supplier_name.strip().lower().replace(" ", "_")

    doc = Document(
        workspace_id=ws.id,
        type="purchase_order",
        filename=req.filename,
        file_path=temp_path,
        sha256=sha256,
        supplier_name=supplier_name,
        supplier_key=supplier_key,
        document_number=po_number,
        currency=req.currency,
        parse_status="completed",
        parse_warnings=parsed["warnings"]
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    po = PurchaseOrder(
        workspace_id=ws.id,
        document_id=doc.id,
        po_number=po_number,
        supplier_name=supplier_name,
        supplier_key=supplier_key,
        currency=req.currency,
        status="open"
    )
    db.add(po)
    db.commit()
    db.refresh(po)

    for item in parsed["lines"]:
        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            line_number=item["line_number"],
            sku=item.get("sku"),
            description=item["description"],
            quantity=item["quantity"],
            unit=item.get("unit", "each"),
            unit_price=item["unit_price"],
            discount=0.0,
            tax_rate=0.0,
            total_price=item.get("total_price")
        )
        db.add(line)

    db.commit()
    db.refresh(po)
    return po


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_authorized_workspace(workspace_id, user, db)
    query = db.query(Document).filter(Document.workspace_id == workspace_id)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/invoices", response_model=List[InvoiceResponse])
def list_invoices(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_authorized_workspace(workspace_id, user, db)
    query = db.query(Invoice).filter(Invoice.workspace_id == workspace_id)
    return query.order_by(Invoice.created_at.desc()).all()


@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(workspace_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_authorized_workspace(workspace_id, user, db)
    query = db.query(PurchaseOrder).filter(PurchaseOrder.workspace_id == workspace_id)
    return query.order_by(PurchaseOrder.created_at.desc()).all()
