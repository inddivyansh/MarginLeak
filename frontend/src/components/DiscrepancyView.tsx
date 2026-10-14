import React, { useState } from 'react';
import { api, Finding, DisputeDraft } from '../api/client';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, XCircle, Mail, ChevronDown, ChevronUp, FileText, Check } from 'lucide-react';
import { DisputeDraftModal } from './DisputeDraftModal';

interface DiscrepancyViewProps {
  findings: Finding[];
  workspaceId: string;
  onUpdateStatus: (id: string, status: string, note?: string) => Promise<void>;
}

export const DiscrepancyView: React.FC<DiscrepancyViewProps> = ({ findings, workspaceId, onUpdateStatus }) => {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [dismissNoteId, setDismissNoteId] = useState<string | null>(null);
  const [dismissNoteText, setDismissNoteText] = useState<string>('');
  const [draft, setDraft] = useState<DisputeDraft | null>(null);
  const [draftLoadingId, setDraftLoadingId] = useState<string | null>(null);

  const handleDraft = async (findingId: string) => {
    setDraftLoadingId(findingId);
    try {
      setDraft(await api.getDisputeDraft(findingId, workspaceId));
    } finally {
      setDraftLoadingId(null);
    }
  };

  const filtered = findings.filter(f => {
    if (filterType !== 'ALL' && f.type !== filterType) return false;
    if (filterStatus !== 'ALL' && f.status !== filterStatus) return false;
    return true;
  });

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'PRICE_MISMATCH':
        return 'Price Variance';
      case 'QUANTITY_MISMATCH':
        return 'Quantity Variance';
      case 'HISTORICAL_PRICE_ANOMALY':
        return 'Historical Price Spike';
      case 'DUPLICATE_CANDIDATE':
        return 'Duplicate Billing';
      case 'AMBIGUOUS_MATCH':
        return 'Line Discrepancy';
      case 'UNMATCHED_LINE':
        return 'Unmatched Line';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  const handleDismissSubmit = (id: string) => {
    onUpdateStatus(id, 'dismissed', dismissNoteText || 'Authorized supplier exception');
    setDismissNoteId(null);
    setDismissNoteText('');
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div>
      {/* Expensify Filter Toolbar */}
      <div className="exceptions-toolbar">
        <div className="filter-pills-row">
          <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700, textTransform: 'uppercase', marginRight: '0.25rem' }}>
            Filter:
          </span>
          {[
            { id: 'ALL', label: 'All Items' },
            { id: 'PRICE_MISMATCH', label: 'Price Variances' },
            { id: 'QUANTITY_MISMATCH', label: 'Quantity Excess' },
            { id: 'DUPLICATE_CANDIDATE', label: 'Duplicates' },
            { id: 'HISTORICAL_PRICE_ANOMALY', label: 'Price Spikes' }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setFilterType(t.id)}
              className={`filter-pill ${filterType === t.id ? 'active' : ''}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="filter-pills-row">
          <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 700, textTransform: 'uppercase', marginRight: '0.25rem' }}>
            Status:
          </span>
          {[
            { id: 'ALL', label: 'All' },
            { id: 'open', label: 'Action Required' },
            { id: 'confirmed', label: 'Confirmed' },
            { id: 'dismissed', label: 'Approved' }
          ].map(s => (
            <button
              key={s.id}
              onClick={() => setFilterStatus(s.id)}
              className={`filter-pill ${filterStatus === s.id ? 'active' : ''}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Expense-Style Discrepancy Ledger Feed */}
      {filtered.length === 0 ? (
        <div style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
          <CheckCircle2 size={36} color="#03d47c" style={{ margin: '0 auto 0.75rem' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>All Invoiced Items Reconciled</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            No unresolved pricing or quantity exceptions found matching the selected filter.
          </p>
        </div>
      ) : (
        <div className="expense-feed">
          {filtered.map(f => {
            const ev = f.evidence_json || {};
            const isExpanded = expandedId === f.id;
            const isDismissing = dismissNoteId === f.id;

            return (
              <div key={f.id} className="expense-row-item">
                <div className="expense-main-line" onClick={() => toggleExpand(f.id)}>
                  {/* Left Column: Indicator, Type, Summary */}
                  <div className="expense-left-col">
                    <div className={`expense-indicator ${f.severity}`} />
                    <div className="expense-info-block">
                      <div className="expense-title-row">
                        <span className="expense-type-badge">{getTypeLabel(f.type)}</span>
                        <span className="expense-headline">
                          {f.explanation.split('.')[0]}
                        </span>
                      </div>
                      <div className="expense-abstract-desc">
                        {f.explanation.includes('.') 
                          ? f.explanation.split('.').slice(1).join('.').trim() 
                          : f.explanation}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Amount, Status Pill, Action Buttons */}
                  <div className="expense-right-col" onClick={(e) => e.stopPropagation()}>
                    {f.amount_at_risk > 0 && (
                      <div className="expense-amount-block">
                        <span className="expense-overcharge-val">
                          +${f.amount_at_risk.toFixed(2)}
                        </span>
                        <span className="expense-overcharge-label">Overcharge</span>
                      </div>
                    )}

                    <div>
                      {f.status === 'open' && (
                        <span className="badge badge-warning">Action Required</span>
                      )}
                      {f.status === 'confirmed' && (
                        <span className="badge badge-danger">Dispute Pending</span>
                      )}
                      {f.status === 'dismissed' && (
                        <span className="badge badge-success">Approved</span>
                      )}
                    </div>

                    <div className="expense-actions-bar">
                      {f.status === 'open' && (
                        <>
                          <button
                            className="btn btn-sm btn-accent"
                            onClick={() => onUpdateStatus(f.id, 'confirmed')}
                            title="Confirm overcharge and flag for vendor credit"
                          >
                            <AlertCircle size={13} />
                            <span>Confirm</span>
                          </button>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => setDismissNoteId(isDismissing ? null : f.id)}
                            title="Approve variance or dismiss"
                          >
                            <XCircle size={13} />
                            <span>Dismiss</span>
                          </button>
                        </>
                      )}

                      {f.status === 'confirmed' && (
                        <>
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleDraft(f.id)}
                            disabled={draftLoadingId === f.id}
                            title="Generate professional supplier credit letter"
                          >
                            <Mail size={13} />
                            <span>{draftLoadingId === f.id ? 'Drafting...' : 'Dispute Letter'}</span>
                          </button>
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => onUpdateStatus(f.id, 'resolved', 'Handled via credit memo')}
                            title="Mark as resolved"
                          >
                            <Check size={13} color="#03d47c" />
                            <span>Resolved</span>
                          </button>
                        </>
                      )}

                      {f.status === 'dismissed' && (
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => onUpdateStatus(f.id, 'open')}
                          title="Re-open for audit review"
                        >
                          <span>Re-open</span>
                        </button>
                      )}

                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => toggleExpand(f.id)}
                        title="Toggle audit evidence comparison"
                        style={{ padding: '0.35rem 0.45rem' }}
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Dismissal Reason Form */}
                {isDismissing && (
                  <div style={{
                    padding: '0.85rem 1.25rem 0.85rem 2.85rem',
                    background: '#09121e',
                    borderTop: '1px solid var(--border-subtle)',
                    display: 'flex',
                    gap: '0.65rem',
                    alignItems: 'center',
                    flexWrap: 'wrap'
                  }}>
                    <input
                      type="text"
                      placeholder="Reason for approving adjustment (e.g. Authorized freight surcharge)..."
                      value={dismissNoteText}
                      onChange={(e) => setDismissNoteText(e.target.value)}
                      style={{
                        flex: '1 1 240px',
                        padding: '0.45rem 0.75rem',
                        borderRadius: '4px',
                        border: '1px solid var(--border-subtle)',
                        background: 'var(--bg-input)',
                        color: '#fff',
                        fontSize: '0.825rem'
                      }}
                    />
                    <button className="btn btn-sm btn-primary" onClick={() => handleDismissSubmit(f.id)}>
                      Approve & Dismiss
                    </button>
                    <button className="btn btn-sm btn-secondary" onClick={() => setDismissNoteId(null)}>
                      Cancel
                    </button>
                  </div>
                )}

                {/* Expandable Clean Audit Evidence Drawer (Clean, Abstract, Expensify-Style) */}
                {isExpanded && (
                  <div className="expense-evidence-drawer">
                    <div className="evidence-comparison-grid">
                      {ev.expected_amount !== undefined && (
                        <div className="comparison-box">
                          <div className="comparison-header">Authorized Purchase Order</div>
                          <div className="comparison-val">
                            ${Number(ev.expected_amount).toFixed(2)}
                          </div>
                          <div className="comparison-sub">Contract baseline</div>
                        </div>
                      )}

                      {ev.billed_amount !== undefined && (
                        <div className="comparison-box">
                          <div className="comparison-header">Billed Invoice Amount</div>
                          <div className="comparison-val" style={{ color: '#fda4af' }}>
                            ${Number(ev.billed_amount).toFixed(2)}
                          </div>
                          <div className="comparison-sub">Amount charged</div>
                        </div>
                      )}

                      {ev.difference !== undefined && (
                        <div className="comparison-box">
                          <div className="comparison-header">Net Discrepancy</div>
                          <div className="comparison-val" style={{ color: '#f43f5e' }}>
                            +${Number(ev.difference).toFixed(2)}
                          </div>
                          <div className="comparison-sub">Identified leakage</div>
                        </div>
                      )}
                    </div>

                    {ev.invoice_snippet && (
                      <div className="evidence-source-snippet">
                        Source Reference (Invoice Page {ev.invoice_page || 1}): &ldquo;{ev.invoice_snippet}&rdquo;
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {draft && <DisputeDraftModal draft={draft} onClose={() => setDraft(null)} />}
    </div>
  );
};
