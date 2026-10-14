const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) window.dispatchEvent(new Event('marginleak-auth-expired'));
  return response;
}

async function handleResponse<T = any>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `Request failed (${res.status} ${res.statusText})`;
    try {
      const err = await res.json();
      detail = err.detail || err.message || detail;
    } catch {
      const text = await res.text().catch(() => '');
      if (text) {
        detail = text.slice(0, 200).trim();
      }
    }
    throw new Error(detail);
  }
  return res.json();
}

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
  supplier_key?: string;
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

export interface SupplierRisk {
  supplier_key: string;
  supplier_name?: string;
  risk_level: 'low' | 'medium' | 'high';
  overbilling_probability: number;
  heuristic_risk_score?: number;
  risk_score_type?: string;
  is_calibrated_probability?: boolean;
  dispute_win_probability: number;
  model_provider: string;
  sample_count: number;
  features: Record<string, number>;
}

export interface DisputeDraft {
  subject: string;
  body: string;
  amount_at_risk: number;
  currency: string;
  invoice_number: string;
  po_number?: string;
}

export const api = {
  async getWorkspace(): Promise<{ id: string; name: string; default_currency: string }> {
    const res = await apiFetch(`${API_BASE}/workspaces/default`);
    return handleResponse(res);
  },

  async getReconciliations(workspaceId: string): Promise<Reconciliation[]> {
    const res = await apiFetch(`${API_BASE}/reconciliations?workspace_id=${encodeURIComponent(workspaceId)}`);
    return handleResponse(res);
  },

  async getReconciliation(id: string, workspaceId: string): Promise<Reconciliation> {
    const res = await apiFetch(`${API_BASE}/reconciliations/${id}?workspace_id=${encodeURIComponent(workspaceId)}`);
    return handleResponse(res);
  },

  async updateFindingStatus(id: string, status: string, workspaceId: string, note?: string): Promise<Finding> {
    const res = await apiFetch(`${API_BASE}/findings/${id}?workspace_id=${encodeURIComponent(workspaceId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ status, note })
    });
    return handleResponse(res);
  },

  async correctLineMatch(id: string, workspaceId: string, poLineId?: string, markUnmatched = false, note?: string): Promise<any> {
    const res = await apiFetch(`${API_BASE}/line-matches/${id}?workspace_id=${encodeURIComponent(workspaceId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ po_line_id: poLineId, mark_unmatched: markUnmatched, note })
    });
    return handleResponse(res);
  },

  async getPriceHistory(workspaceId: string): Promise<HistoricalPriceItem[]> {
    const res = await apiFetch(`${API_BASE}/history/prices?workspace_id=${encodeURIComponent(workspaceId)}`);
    return handleResponse(res);
  },

  async getSupplierRisk(supplierKey?: string, workspaceId?: string): Promise<SupplierRisk> {
    const params = new URLSearchParams();
    if (supplierKey) params.set('supplier_key', supplierKey);
    if (workspaceId) params.set('workspace_id', workspaceId);
    const res = await apiFetch(`${API_BASE}/supplier-risk?${params.toString()}`);
    return handleResponse(res);
  },

  async getDisputeDraft(findingId: string, workspaceId: string): Promise<DisputeDraft> {
    const res = await apiFetch(`${API_BASE}/findings/${findingId}/dispute-draft?workspace_id=${encodeURIComponent(workspaceId)}`);
    return handleResponse(res);
  },

  async getBenchmark(): Promise<BenchmarkData> {
    const res = await apiFetch(`${API_BASE}/evaluations/latest`);
    return handleResponse(res);
  },

  async testNormalize(description: string, sku = ''): Promise<any> {
    const res = await apiFetch(`${API_BASE}/evaluations/normalize-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ description, sku })
    });
    return handleResponse(res);
  },

  async seedDemoScenario(): Promise<any> {
    const res = await apiFetch(`${API_BASE}/demo/seed-sample-scenario`, { method: 'POST' });
    return handleResponse(res);
  },

  async uploadInvoicePdf(file: File, workspaceId?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (workspaceId) formData.append('workspace_id', workspaceId);
    const res = await apiFetch(`${API_BASE}/documents/invoices`, {
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
    const res = await apiFetch(`${API_BASE}/purchase-orders/import`, {
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
    temp_key: string;
    po_number?: string;
    supplier_name?: string;
    currency?: string;
    columns: Record<string, string>;
  }): Promise<any> {
    const res = await apiFetch(`${API_BASE}/purchase-orders/confirm-import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody(data)
    });
    return handleResponse(res);
  },

  getReportDownloadUrl(reconciliationId: string, workspaceId: string): string {
    return `${API_BASE}/reports/${reconciliationId}.csv?workspace_id=${encodeURIComponent(workspaceId)}`;
  },

  async downloadReport(reconciliationId: string, workspaceId: string): Promise<void> {
    const url = this.getReportDownloadUrl(reconciliationId, workspaceId);
    const res = await apiFetch(url);
    if (!res.ok) {
      if (res.status === 401) {
        throw new Error('Unauthorized (401): Authentication required to export reports.');
      }
      if (res.status === 404) {
        throw new Error('Not Found (404): Reconciliation report could not be found.');
      }
      let detail = `Failed to download report (${res.status} ${res.statusText})`;
      try {
        const err = await res.json();
        detail = err.detail || err.message || detail;
      } catch {
        const text = await res.text().catch(() => '');
        if (text) detail = text.slice(0, 200).trim();
      }
      throw new Error(detail);
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `MarginLeak_Exception_Report_${reconciliationId.slice(0, 8)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
  }
};

function jsonBody(obj: any): string {
  return JSON.stringify(obj);
}
