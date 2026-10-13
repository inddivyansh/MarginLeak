const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export interface Finding {
  id: string;
  reconciliation_id: string;
  invoice_line_id?: string;
  po_line_id?: string;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  amount_at_risk: number;
  currency: string;
  explanation: string;
  evidence_json: Record<string, any>;
  status: 'open' | 'confirmed' | 'dismissed' | 'resolved';
  created_at: string;
}

export interface LineMatch {
  id: string;
  reconciliation_id: string;
  invoice_line_id: string;
  po_line_id?: string;
  method: string;
  confidence: number;
  review_status: string;
  invoice_line?: {
    line_number: number;
    sku?: string;
    description: string;
    quantity: number;
    unit: string;
    unit_price: number;
    total_price: number;
    source_page: number;
    source_text?: string;
  };
  po_line?: {
    line_number: number;
    sku?: string;
    description: string;
    quantity: number;
    unit: string;
    unit_price: number;
    total_price: number;
  };
}

export interface Reconciliation {
  id: string;
  workspace_id: string;
  invoice_id: string;
  purchase_order_id?: string;
  status: string;
  amount_at_risk: number;
  currency: string;
  matched_lines_count: number;
  ambiguous_lines_count: number;
  unmatched_lines_count: number;
  findings_count: number;
  created_at: string;
  findings: Finding[];
  matches: LineMatch[];
}

export interface HistoricalPriceItem {
  supplier_key: string;
  item_normalized: string;
  currency: string;
  unit: string;
  purchase_count: number;
  median_unit_price: number;
  min_unit_price: number;
  max_unit_price: number;
  latest_unit_price: number;
  latest_purchase_date?: string;
  price_history: Array<{ price: number; date: string; invoice_number: string; quantity: number }>;
}

export interface BenchmarkData {
  model_name: string;
  dataset_version: string;
  config: Record<string, any>;
  metrics: {
    baseline_a_deterministic: any;
    baseline_b_base_model: any;
    candidate_c_tinker_lora: any;
  };
  improvements: {
    field_accuracy_gain_pts: number;
    false_merge_reduction_pct: number;
    json_reliability_gain_pts: number;
    precision_gain_pts?: number;
  };
  sample_comparisons: any[];
}

export const api = {
  async getWorkspace(): Promise<{ id: string; name: string; default_currency: string }> {
    const res = await fetch(`${API_BASE}/workspaces/default`);
    return res.json();
  },

  async getReconciliations(): Promise<Reconciliation[]> {
    const res = await fetch(`${API_BASE}/reconciliations`);
    return res.json();
  },

  async getReconciliation(id: string): Promise<Reconciliation> {
    const res = await fetch(`${API_BASE}/reconciliations/${id}`);
    return res.json();
  },

  async updateFindingStatus(id: string, status: string, note?: string): Promise<Finding> {
    const res = await fetch(`${API_BASE}/findings/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ status, note })
    });
    return res.json();
  },

  async correctLineMatch(id: string, poLineId?: string, markUnmatched = false, note?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/line-matches/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ po_line_id: poLineId, mark_unmatched: markUnmatched, note })
    });
    return res.json();
  },

  async getPriceHistory(): Promise<HistoricalPriceItem[]> {
    const res = await fetch(`${API_BASE}/history/prices`);
    return res.json();
  },

  async getBenchmark(): Promise<BenchmarkData> {
    const res = await fetch(`${API_BASE}/evaluations/latest`);
    return res.json();
  },

  async testNormalize(description: string, sku = ''): Promise<any> {
    const res = await fetch(`${API_BASE}/evaluations/normalize-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ description, sku })
    });
    return res.json();
  },

  async seedDemoScenario(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/seed-sample-scenario`, { method: 'POST' });
    return res.json();
  },

  async uploadInvoicePdf(file: File, workspaceId?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (workspaceId) formData.append('workspace_id', workspaceId);
    const res = await fetch(`${API_BASE}/documents/invoices`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async previewPo(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/purchase-orders/import`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Import preview failed' }));
      throw new Error(err.detail || 'Import preview failed');
    }
    return res.json();
  },

  async confirmPo(data: {
    workspace_id: string;
    filename: string;
    po_number?: string;
    supplier_name?: string;
    currency?: string;
    columns: Record<string, string>;
  }): Promise<any> {
    const res = await fetch(`${API_BASE}/purchase-orders/confirm-import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody(data)
    });
    return res.json();
  },

  getReportDownloadUrl(reconciliationId: string): string {
    return `${API_BASE}/reports/${reconciliationId}.csv`;
  }
};

function jsonBody(obj: any): string {
  return JSON.stringify(obj);
}
