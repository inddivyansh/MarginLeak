import React, { useState } from 'react';
import { Copy, ExternalLink, Mail, X } from 'lucide-react';
import { DisputeDraft } from '../api/client';

interface DisputeDraftModalProps {
  draft: DisputeDraft;
  onClose: () => void;
}

export const DisputeDraftModal: React.FC<DisputeDraftModalProps> = ({ draft, onClose }) => {
  const [copied, setCopied] = useState(false);

  const copyDraft = async () => {
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const mailto = `mailto:?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(draft.body)}`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Mail size={18} color="#38bdf8" />
              <h2 style={{ margin: 0 }}>Supplier Dispute Letter</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', margin: '0.45rem 0 0', fontSize: '0.82rem' }}>
              Credit memo request for invoice {draft.invoice_number}
            </p>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close dispute letter">
            <X size={20} />
          </button>
        </div>

        <label className="modal-field-label">SUBJECT</label>
        <input className="modal-text-input" value={draft.subject} readOnly />
        <label className="modal-field-label">MESSAGE</label>
        <textarea className="modal-textarea" value={draft.body} readOnly rows={16} />

        <div className="modal-footer-actions">
          <button className="btn btn-secondary" onClick={copyDraft}>
            <Copy size={14} />
            <span>{copied ? 'Copied' : 'Copy Letter'}</span>
          </button>
          <a className="btn btn-primary" href={mailto}>
            <ExternalLink size={14} />
            <span>Open in Email</span>
          </a>
        </div>
      </div>
    </div>
  );
};