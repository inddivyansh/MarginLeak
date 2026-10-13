import React, { useState } from 'react';
import { api } from '../api/client';
import { X, FileText, FileSpreadsheet, Upload, CheckCircle2, AlertCircle } from 'lucide-react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string;
  onSuccess: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, workspaceId, onSuccess }) => {
  const [tab, setTab] = useState<'invoice' | 'po'>('invoice');
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [poPreview, setPoPreview] = useState<any>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleInvoiceUpload = async () => {
    if (!file) return;
    setIsLoading(true);
    setError(null);
    try {
      await api.uploadInvoicePdf(file, workspaceId);
      onSuccess();
      onClose();
    } catch (e: any) {
      setError(e.message || 'Invoice PDF upload and parsing failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePoPreview = async () => {
    if (!file) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.previewPo(file);
      setPoPreview(res);
    } catch (e: any) {
      setError(e.message || 'Purchase Order import failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePoConfirm = async () => {
    if (!poPreview) return;
    setIsLoading(true);
    setError(null);
    try {
      await api.confirmPo({
        workspace_id: workspaceId,
        filename: poPreview.filename,
        temp_key: poPreview.temp_key,
        po_number: poPreview.po_number,
        columns: poPreview.detected_columns
      });
      onSuccess();
      onClose();
    } catch (e: any) {
      setError(e.message || 'Purchase Order confirmation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Upload Accounts Payable Records</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Add supplier PDF invoices or purchase order spreadsheets to reconcile.
            </p>
          </div>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Tab switch */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <button
            className={`btn btn-sm ${tab === 'invoice' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setTab('invoice'); setFile(null); setError(null); setPoPreview(null); }}
            style={{ flex: 1 }}
          >
            <FileText size={15} />
            <span>Supplier Invoice (PDF)</span>
          </button>
          <button
            className={`btn btn-sm ${tab === 'po' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => { setTab('po'); setFile(null); setError(null); setPoPreview(null); }}
            style={{ flex: 1 }}
          >
            <FileSpreadsheet size={15} />
            <span>Purchase Order (CSV/XLSX)</span>
          </button>
        </div>

        {error && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger)',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            marginBottom: '1rem',
            color: '#fca5a5',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Upload Dropzone */}
        {!poPreview && (
          <div>
            <label className="dropzone" style={{ display: 'block' }}>
              <input
                type="file"
                accept={tab === 'invoice' ? '.pdf' : '.csv,.xlsx,.xls'}
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <Upload size={32} color="#6366f1" style={{ margin: '0 auto 0.75rem' }} />
              <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                {file ? file.name : `Click or drag ${tab === 'invoice' ? 'PDF invoice' : 'PO CSV/Excel'} here`}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.35rem' }}>
                {tab === 'invoice' ? 'Selectable text PDF up to 15MB' : 'CSV, XLSX, or XLS spreadsheets up to 10MB'}
              </div>
            </label>

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button className="btn btn-secondary" onClick={onClose} disabled={isLoading}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={tab === 'invoice' ? handleInvoiceUpload : handlePoPreview}
                disabled={!file || isLoading}
              >
                {isLoading ? 'Processing...' : (tab === 'invoice' ? 'Extract & Parse Invoice' : 'Preview Spreadsheet Columns')}
              </button>
            </div>
          </div>
        )}

        {/* PO Column Mapping Confirmation */}
        {poPreview && (
          <div>
            <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '8px', padding: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: 700, marginBottom: '0.5rem' }}>
                <CheckCircle2 size={16} />
                <span>Detected {poPreview.lines_count} PO Lines in {poPreview.filename}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                PO Reference: <strong>{poPreview.po_number}</strong>
              </div>
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', fontWeight: 600, marginBottom: '0.5rem' }}>
              DETECTED COLUMN MAPPINGS:
            </div>
            <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', marginBottom: '1.5rem' }}>
              {Object.entries(poPreview.detected_columns).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                  <span style={{ color: '#94a3b8' }}>{k}:</span>
                  <span style={{ color: '#38bdf8' }}>"{String(v)}"</span>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button className="btn btn-secondary" onClick={() => setPoPreview(null)}>Back</button>
              <button className="btn btn-primary" onClick={handlePoConfirm} disabled={isLoading}>
                {isLoading ? 'Importing...' : 'Confirm & Save Purchase Order'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
