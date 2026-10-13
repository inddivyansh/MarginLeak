import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean,
    DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    default_currency = Column(String(10), default="USD", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="workspace", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="workspace", cascade="all, delete-orphan")
    reconciliations = relationship("Reconciliation", back_populates="workspace", cascade="all, delete-orphan")
    aliases = relationship("SupplierItemAlias", back_populates="workspace", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'invoice' or 'purchase_order'
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    sha256 = Column(String(64), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    supplier_key = Column(String(255), nullable=True, index=True)
    document_number = Column(String(100), nullable=True, index=True)
    document_date = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    parse_status = Column(String(50), default="completed", nullable=False)  # pending, completed, failed
    parse_warnings = Column(JSON, default=list, nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="documents")
    invoices = relationship("Invoice", back_populates="document", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_doc_workspace_sha", "workspace_id", "sha256"),
        Index("idx_doc_workspace_supp_num", "workspace_id", "supplier_key", "document_number"),
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    po_number = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    supplier_key = Column(String(255), nullable=True, index=True)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), default="open", nullable=False)  # open, closed, partially_fulfilled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="purchase_orders")
    document = relationship("Document", back_populates="purchase_orders")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    reconciliations = relationship("Reconciliation", back_populates="purchase_order")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    normalized_description = Column(Text, nullable=True)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(50), default="each", nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    discount = Column(Numeric(12, 4), default=0, nullable=False)
    tax_rate = Column(Numeric(6, 4), default=0, nullable=False)
    total_price = Column(Numeric(12, 4), nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    line_matches = relationship("LineMatch", back_populates="po_line")
    findings = relationship("Finding", back_populates="po_line")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=True)
    supplier_key = Column(String(255), nullable=True, index=True)
    invoice_date = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    subtotal = Column(Numeric(12, 4), nullable=True)
    tax_amount = Column(Numeric(12, 4), default=0, nullable=True)
    freight_amount = Column(Numeric(12, 4), default=0, nullable=True)
    total_amount = Column(Numeric(12, 4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="invoices")
    document = relationship("Document", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    reconciliations = relationship("Reconciliation", back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    normalized_description = Column(Text, nullable=True)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(50), default="each", nullable=False)
    unit_price = Column(Numeric(12, 4), nullable=False)
    discount = Column(Numeric(12, 4), default=0, nullable=False)
    tax_rate = Column(Numeric(6, 4), default=0, nullable=False)
    total_price = Column(Numeric(12, 4), nullable=True)
    source_page = Column(Integer, default=1, nullable=False)
    source_text = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="lines")
    line_matches = relationship("LineMatch", back_populates="invoice_line")
    findings = relationship("Finding", back_populates="invoice_line")


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True, index=True)
    status = Column(String(50), default="completed", nullable=False)  # pending, processing, completed, error
    amount_at_risk = Column(Numeric(12, 4), default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    matched_lines_count = Column(Integer, default=0, nullable=False)
    ambiguous_lines_count = Column(Integer, default=0, nullable=False)
    unmatched_lines_count = Column(Integer, default=0, nullable=False)
    findings_count = Column(Integer, default=0, nullable=False)
    options = Column(JSON, default=dict, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    @property
    def supplier_key(self):
        return self.invoice.supplier_key if self.invoice else None

    workspace = relationship("Workspace", back_populates="reconciliations")
    invoice = relationship("Invoice", back_populates="reconciliations")
    purchase_order = relationship("PurchaseOrder", back_populates="reconciliations")
    matches = relationship("LineMatch", back_populates="reconciliation", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="reconciliation", cascade="all, delete-orphan")


class LineMatch(Base):
    __tablename__ = "line_matches"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    reconciliation_id = Column(String(36), ForeignKey("reconciliations.id"), nullable=False, index=True)
    invoice_line_id = Column(String(36), ForeignKey("invoice_lines.id"), nullable=False)
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id"), nullable=True)
    method = Column(String(50), nullable=False)  # 'exact_sku', 'supplier_alias', 'fuzzy_token', 'model_normalization', 'manual'
    confidence = Column(Numeric(5, 4), default=1.0, nullable=False)  # 0.0000 to 1.0000
    review_status = Column(String(50), default="auto_matched", nullable=False)  # auto_matched, confirmed, corrected, unmatched

    reconciliation = relationship("Reconciliation", back_populates="matches")
    invoice_line = relationship("InvoiceLine", back_populates="line_matches")
    po_line = relationship("PurchaseOrderLine", back_populates="line_matches")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    reconciliation_id = Column(String(36), ForeignKey("reconciliations.id"), nullable=False, index=True)
    invoice_line_id = Column(String(36), ForeignKey("invoice_lines.id"), nullable=True)
    po_line_id = Column(String(36), ForeignKey("purchase_order_lines.id"), nullable=True)
    type = Column(String(50), nullable=False)  # 'PRICE_MISMATCH', 'QUANTITY_MISMATCH', 'HISTORICAL_PRICE_ANOMALY', 'DUPLICATE_CANDIDATE', 'AMBIGUOUS_MATCH', 'UNMATCHED_LINE'
    severity = Column(String(50), default="warning", nullable=False)  # 'info', 'warning', 'critical'
    amount_at_risk = Column(Numeric(12, 4), default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_json = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="open", nullable=False)  # 'open', 'confirmed', 'dismissed', 'resolved'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reconciliation = relationship("Reconciliation", back_populates="findings")
    invoice_line = relationship("InvoiceLine", back_populates="findings")
    po_line = relationship("PurchaseOrderLine", back_populates="findings")
    review_events = relationship("ReviewEvent", back_populates="finding", cascade="all, delete-orphan")


class ReviewEvent(Base):
    __tablename__ = "review_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=False, index=True)
    actor_id = Column(String(100), default="user", nullable=False)
    action = Column(String(50), nullable=False)  # 'confirm', 'dismiss', 'resolve', 'correct_match', 'add_note'
    old_value_json = Column(JSON, nullable=True)
    new_value_json = Column(JSON, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    finding = relationship("Finding", back_populates="review_events")


class SupplierItemAlias(Base):
    __tablename__ = "supplier_item_aliases"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    supplier_key = Column(String(255), nullable=False, index=True)
    alias_normalized = Column(String(255), nullable=False, index=True)
    canonical_item_key = Column(String(255), nullable=False)
    canonical_description = Column(Text, nullable=True)
    unit = Column(String(50), default="each", nullable=False)
    created_from = Column(String(50), default="user_correction", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="aliases")

    __table_args__ = (
        Index("idx_alias_lookup", "workspace_id", "supplier_key", "alias_normalized"),
    )


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    model_name = Column(String(100), nullable=False)
    dataset_version = Column(String(50), nullable=False)
    config_json = Column(JSON, default=dict, nullable=False)
    metrics_json = Column(JSON, default=dict, nullable=False)
    sample_outputs_json = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
