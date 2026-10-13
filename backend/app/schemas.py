from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    default_currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    type: str
    filename: str
    supplier_name: Optional[str] = None
    supplier_key: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    currency: str
    parse_status: str
    parse_warnings: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class POLineSchema(BaseModel):
    line_number: int
    sku: Optional[str] = None
    description: str
    normalized_description: Optional[str] = None
    quantity: float
    unit: str = "each"
    unit_price: float
    discount: float = 0.0
    tax_rate: float = 0.0
    total_price: Optional[float] = None


class PurchaseOrderResponse(BaseModel):
    id: str
    workspace_id: str
    document_id: Optional[str] = None
    po_number: str
    supplier_name: Optional[str] = None
    currency: str
    status: str
    lines: List[POLineSchema] = []
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceLineSchema(BaseModel):
    id: Optional[str] = None
    line_number: int
    sku: Optional[str] = None
    description: str
    normalized_description: Optional[str] = None
    quantity: float
    unit: str = "each"
    unit_price: float
    discount: float = 0.0
    tax_rate: float = 0.0
    total_price: Optional[float] = None
    source_page: int = 1
    source_text: Optional[str] = None

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: str
    workspace_id: str
    document_id: Optional[str] = None
    invoice_number: str
    supplier_name: Optional[str] = None
    supplier_key: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: str
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = 0.0
    freight_amount: Optional[float] = 0.0
    total_amount: float
    lines: List[InvoiceLineSchema] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ColumnMappingRequest(BaseModel):
    workspace_id: str
    filename: str
    supplier_name: Optional[str] = None
    po_number: Optional[str] = None
    currency: str = "USD"
    columns: Dict[str, str]  # e.g. {"sku": "SKU", "description": "Item Description", "quantity": "Qty", "unit_price": "Unit Cost", "unit": "Unit"}


class ReconciliationCreateRequest(BaseModel):
    workspace_id: str
    invoice_id: str
    purchase_order_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = Field(default_factory=lambda: {
        "historical_price_check": True,
        "price_tolerance_percent": 2.0,
        "historical_alert_percent": 5.0,
        "use_model_normalization": True
    })


class FindingEvidence(BaseModel):
    invoice_line_num: Optional[int] = None
    invoice_sku: Optional[str] = None
    invoice_desc: Optional[str] = None
    invoice_unit_price: Optional[float] = None
    invoice_qty: Optional[float] = None
    invoice_unit: Optional[str] = None
    invoice_snippet: Optional[str] = None
    invoice_page: Optional[int] = 1

    po_line_num: Optional[int] = None
    po_sku: Optional[str] = None
    po_desc: Optional[str] = None
    po_unit_price: Optional[float] = None
    po_qty: Optional[float] = None
    po_unit: Optional[str] = None

    calculation_formula: Optional[str] = None
    expected_amount: Optional[float] = None
    billed_amount: Optional[float] = None
    difference: Optional[float] = None
    historical_baseline_price: Optional[float] = None
    historical_sample_count: Optional[int] = None
    matched_method: Optional[str] = None
    match_confidence: Optional[float] = None


class FindingResponse(BaseModel):
    id: str
    reconciliation_id: str
    invoice_line_id: Optional[str] = None
    po_line_id: Optional[str] = None
    type: str  # 'PRICE_MISMATCH', 'QUANTITY_MISMATCH', 'HISTORICAL_PRICE_ANOMALY', 'DUPLICATE_CANDIDATE', 'AMBIGUOUS_MATCH', 'UNMATCHED_LINE'
    severity: str  # 'info', 'warning', 'critical'
    amount_at_risk: float
    currency: str
    explanation: str
    evidence_json: Dict[str, Any]
    status: str  # 'open', 'confirmed', 'dismissed', 'resolved'
    created_at: datetime

    class Config:
        from_attributes = True


class LineMatchResponse(BaseModel):
    id: str
    reconciliation_id: str
    invoice_line_id: str
    po_line_id: Optional[str] = None
    method: str
    confidence: float
    review_status: str
    invoice_line: Optional[InvoiceLineSchema] = None
    po_line: Optional[POLineSchema] = None

    class Config:
        from_attributes = True


class ReconciliationResponse(BaseModel):
    id: str
    workspace_id: str
    invoice_id: str
    supplier_key: Optional[str] = None
    purchase_order_id: Optional[str] = None
    status: str
    amount_at_risk: float
    currency: str
    matched_lines_count: int
    ambiguous_lines_count: int
    unmatched_lines_count: int
    findings_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[FindingResponse] = []
    matches: List[LineMatchResponse] = []

    class Config:
        from_attributes = True


class FindingUpdate(BaseModel):
    status: str  # confirmed, dismissed, resolved
    note: Optional[str] = None


class MatchCorrectionUpdate(BaseModel):
    po_line_id: Optional[str] = None
    mark_unmatched: bool = False
    note: Optional[str] = None


class HistoricalPriceItem(BaseModel):
    supplier_key: str
    item_normalized: str
    currency: str
    unit: str
    purchase_count: int
    median_unit_price: float
    min_unit_price: float
    max_unit_price: float
    latest_unit_price: float
    latest_purchase_date: Optional[str] = None
    price_history: List[Dict[str, Any]] = []


class SupplierRiskResponse(BaseModel):
    supplier_key: str
    supplier_name: Optional[str] = None
    risk_level: str
    overbilling_probability: float
    dispute_win_probability: float
    model_provider: str
    sample_count: int
    features: Dict[str, float]


class DisputeDraftResponse(BaseModel):
    subject: str
    body: str
    amount_at_risk: float
    currency: str
    invoice_number: str
    po_number: Optional[str] = None


class EvaluationMetricSummary(BaseModel):
    model_name: str
    exact_structured_field_acc: float
    json_validity_rate: float
    false_merge_rate: float
    match_precision: float
    match_recall: float
    p50_latency_ms: float
    p95_latency_ms: float
    cost_per_1k_lines: float
