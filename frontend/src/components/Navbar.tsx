import React from 'react';
import { ShieldAlert, Cpu, Sparkles, Upload, Download, RefreshCw, LogOut } from 'lucide-react';
import { useAuth } from './AuthGate';

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
  const { user, signOut } = useAuth();

  return (
    <header className="navbar">
      <div className="brand-section">
        <div className="brand-logo-icon">
          <ShieldAlert size={22} color="#ffffff" />
        </div>
        <div className="brand-text">
          <div className="brand-title">MarginLeak</div>
          <div className="brand-tagline">Autonomous AP Leakage Auditor</div>
        </div>
        <div className="badge badge-tinker badge-pulse brand-badge" title="Autonomous AI Audit Engine is actively protecting payments">
          <Cpu size={13} />
          <span className="badge-text-full">AI Audit Guard Active</span>
          <span className="badge-text-compact">AI Guard</span>
        </div>
      </div>

      <div className="nav-actions">
        <div className="badge badge-info nav-workspace-badge" title={workspaceName || 'Acme E-Commerce'}>
          <span className="workspace-name-truncate">{workspaceName || 'Acme E-Commerce'}</span>
        </div>

        <button
          className="btn btn-secondary nav-action-btn"
          onClick={onSeedDemo}
          disabled={isSeeding}
          title="Seed realistic supplier PO & PDF invoice with intentional overcharges"
        >
          {isSeeding ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} color="#f59e0b" />}
          <span>{isSeeding ? 'Seeding...' : 'Load Demo Scenario'}</span>
        </button>

        <button className="btn btn-primary nav-action-btn" onClick={onOpenUpload}>
          <Upload size={15} />
          <span>Upload Records</span>
        </button>

        {hasReconciliation && (
          <button className="btn btn-secondary nav-action-btn" onClick={onExportCsv} title="Export audited discrepancy CSV report">
            <Download size={15} />
            <span>Export CSV</span>
          </button>
        )}

        {user && (
          <button
            className="btn btn-secondary nav-action-btn nav-logout-btn"
            onClick={() => signOut()}
            title={`Signed in as ${user.email || 'user'}. Click to sign out.`}
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </header>
  );
};
