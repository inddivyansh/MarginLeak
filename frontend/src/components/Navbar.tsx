import React from 'react';
import { ShieldAlert, Cpu, Sparkles, Upload, FileSpreadsheet, Download, RefreshCw } from 'lucide-react';

interface NavbarProps {
  workspaceName: string;
  onOpenUpload: () => void;
  onSeedDemo: () => void;
  onExportCsv: () => void;
  isSeeding: boolean;
  hasReconciliation: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  workspaceName,
  onOpenUpload,
  onSeedDemo,
  onExportCsv,
  isSeeding,
  hasReconciliation
}) => {
  return (
    <header className="navbar">
      <div className="brand-section">
        <div className="brand-logo-icon">
          <ShieldAlert size={24} color="#ffffff" />
        </div>
        <div>
          <div className="brand-title">MarginLeak</div>
          <div className="brand-tagline">Autonomous AP Leakage Auditor</div>
        </div>
        <div className="badge badge-tinker badge-pulse" style={{ marginLeft: '0.75rem' }}>
          <Cpu size={13} />
          <span>Tinker LoRA Qwen3-8B</span>
        </div>
      </div>

      <div className="nav-actions">
        <div className="badge badge-info">
          <span>{workspaceName || 'Acme E-Commerce'}</span>
        </div>

        <button
          className="btn btn-secondary"
          onClick={onSeedDemo}
          disabled={isSeeding}
          title="Seed realistic supplier PO & PDF invoice with intentional overcharges"
        >
          {isSeeding ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} color="#f59e0b" />}
          <span>{isSeeding ? 'Seeding...' : 'Load Demo Scenario'}</span>
        </button>

        <button className="btn btn-primary" onClick={onOpenUpload}>
          <Upload size={15} />
          <span>Upload Records</span>
        </button>

        {hasReconciliation && (
          <button className="btn btn-secondary" onClick={onExportCsv} title="Export audited discrepancy CSV report">
            <Download size={15} />
            <span>Export CSV</span>
          </button>
        )}
      </div>
    </header>
  );
};
