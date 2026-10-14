*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

# MarginLeak: Autonomous Accounts-Payable AI Auditor & Margin Recovery System

> **Catch hidden overcharges, quantity discrepancies, and silent price creep before you pay supplier invoices.**  
> Built as an evidence-backed, open-source accounts-payable auditor for small businesses, e-commerce sellers, and recurring B2B buyers.

---

## What I Built

MarginLeak is an open-source, audit-grade accounts-payable auditor and margin-recovery system designed for small e-commerce sellers, independent retail distributors, and recurring B2B buyers.

### The Real-World Problem
Small businesses purchase inventory from dozens of distinct suppliers and receive hundreds of raw invoice lines every month. Because accounting teams and solo founders lack the time to manually cross-check every single line item against purchase orders and historical rates, **accounts-payable leakage silently drains 2% to 8% of net business margins**:

1. **Silent Unit Price Creep**: A supplier quietly hikes a unit price from `$14.50` to `$16.20` (+11.7%). Across a standard 300-unit shipment, that is **$510.00 directly lost from net profit**.
2. **Quantity Over-Billing**: An invoice bills for 150 units when the approved Purchase Order (PO) only authorized 100 units. That represents **hundreds of dollars of unauthorized inventory exposure**.
3. **Duplicate Line Items & Invoices**: The same line item is billed twice across overlapping invoices, or an entire invoice is resubmitted under a slightly altered invoice number.
4. **Semantic Description Chaos**: Traditional spreadsheet `VLOOKUP` or SQL joins fail completely because supplier descriptions never match purchase order catalog names (*"Type C Multi-Port Hub 7P"* vs. *"7-in-1 USB-C Dock Space Gray"*).

### The Solution
MarginLeak turns manual review into an automated, evidence-backed workflow. A user uploads a supplier invoice PDF and an authorized purchase-order spreadsheet. MarginLeak matches invoice lines to purchase-order lines even when descriptions differ, checks historical supplier pricing records, calculates exact financial exposure down to the cent, anchors every discrepancy to the source PDF text, and auto-generates professional supplier dispute letters.

Every finding presented to the user includes:
- **Discrepancy Type & Severity**: Clearly flagged as `PRICE_MISMATCH`, `QUANTITY_MISMATCH`, `DUPLICATE_LINE`, or `HISTORICAL_PRICE_INCREASE`.
- **Exact Amount at Risk**: Computed with zero floating-point error.
- **Transparent Mathematical Formula**: Fully auditable calculation breakdown (e.g., `(Invoice Unit Price $18.50 - PO Unit Price $16.00) × Invoiced Quantity 75 = $187.50`).
- **Source Document Evidence**: The exact invoice page number, raw text block, and bounding-box snippet.
- **Review & Feedback Loop**: One-click actions to confirm, dismiss, resolve, or correct matches. Confirmed corrections are remembered as supplier aliases to improve future reconciliations automatically.
- **Automated Supplier Dispute Generation**: A generated supplier credit-memo request for confirmed findings with itemized proof, copy-to-clipboard, and `mailto:` pre-filling.
- **TabPFN Supplier Risk & Dispute-Win Intelligence**: An empirical assessment of supplier overbilling risk and dispute recovery probability based on historical records.

The primary customer is a small business owner, inventory manager, or bookkeeper processing roughly 50 to 500 invoice lines per month. The product is designed as a focused, high-ROI accounts-payable tool rather than a bloated, enterprise procurement suite.

---

## Demo

* 🌐 **Public Hosted Live Demo**: [https://marginleak.onrender.com/](https://marginleak.onrender.com/)

The deployed application features full Supabase email/password authentication. After signing in, each user is provisioned a completely private, isolated workspace.

### ⚡ The One-Click Demo Scenario
You don't need your own invoice files to evaluate MarginLeak. The live dashboard features a **"Load Demo Scenario"** button that instantly stages:
1. A realistic purchase order spreadsheet with 5 distinct catalog items.
2. An authentic supplier invoice PDF with intentional, real-world discrepancies:
   - **Unit Price Variance**: Item billed at `$18.50` vs PO contracted price of `$16.00`.
   - **Quantity Overage**: Invoiced for 75 units against 50 authorized units.
   - **Historical Price Drift**: Unit price 14% higher than the historical supplier median.
   - **Duplicate Invoiced Line**: An accidental second billing of the same component on line 4.
3. An interactive review workflow: Confirm findings, inspect exact PDF coordinates, view the TabPFN supplier risk badge, and click **"Generate Dispute Letter"** to draft an email directly to the supplier.

---

## Code

* 💻 **GitHub Repository**: [https://github.com/inddivyansh/MarginLeak](https://github.com/inddivyansh/MarginLeak)
* 📜 **License**: [MIT License](https://github.com/inddivyansh/MarginLeak/blob/main/LICENSE)

### Important Implementation Areas:
- **Backend API Core**: [backend/app/main.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/main.py) and [backend/app/api/](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/api/)
- **Deterministic Reconciliation Engine**: [backend/app/engine/reconciliation.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/reconciliation.py)
- **Fuzzy Product Matching**: [backend/app/engine/matcher.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/matcher.py)
- **TabPFN Supplier Risk Classifier**: [backend/app/engine/supplier_risk.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/supplier_risk.py)
- **Tinker Normalization Client**: [backend/app/ai/tinker_client.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/ai/tinker_client.py)
- **Genuine Tinker LoRA Trainer**: [tinker_experiment/train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py)
- **Held-Out Benchmark Runner**: [tinker_experiment/run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py)
- **React Dashboard**: [frontend/src/](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/frontend/src/)
- **Multi-Tenant Auth & Security**: [backend/app/auth.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/auth.py), [backend/app/api/auth.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/api/auth.py), and [frontend/src/components/AuthGate.tsx](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/frontend/src/components/AuthGate.tsx)
- **Production Packaging**: [Dockerfile](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/Dockerfile) and [render.yaml](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/render.yaml)

---

## How I Built It

MarginLeak is built on a foundational rule for financial software: **The Strict Separation of Model Semantics and Deterministic Arithmetic.**

> **Core Architecture Rule**: *The model must never calculate money.* Open-weight models interpret messy supplier descriptions and normalize them into structured attributes; ordinary deterministic Python code calculates every dollar amount and verifies totals.

### 1. Document Extraction & Fuzzy Matching
- **PyMuPDF (`pymupdf`)**: Extracts raw text blocks, line items, and page coordinates from invoice PDFs without OCR latency, enabling exact visual bounding-box citations.
- **Pandas & OpenPyXL**: Ingests purchase order spreadsheets, supporting flexible user-mapped columns (`sku`, `description`, `qty`, `unit_price`, `uom`).
- **RapidFuzz Engine**: Leverages token-sort ratios, SKU alignment, and attribute extraction to resolve variations like *"Type C Multi-Port Hub 7P"* vs *"7-in-1 USB-C Dock Space Gray"*.
- **Supplier Alias Memory**: Auditor corrections are persisted per tenant, automatically teaching the system vendor-specific naming conventions over time.

### 2. Open-Weight Fine-Tuning with Thinking Machines Tinker
To standardize raw vendor descriptions into canonical attributes without hallucinations, MarginLeak implements fine-tuning for `Qwen/Qwen3-8B` using **Thinking Machines' Tinker API** with Low-Rank Adaptation (LoRA).

- **The Task**: Canonical Line-Item Normalization extracts the product identity, pack size (`100`), pack unit (`box`), size (`large`), and specific attributes (`blue`, `nitrile`) into strict JSON.
- **Real SDK Integration**: [train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py) executes genuine LoRA fine-tuning with cross-entropy loss computation, gradient backpropagation, AdamW optimizer steps, and sampler checkpoint export.
- **Deterministic Fallback**: The app includes a rule-based fallback normalizer so the core product remains fully functional offline or when model inference credentials are absent.
- **Benchmark Suite**: [run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py) evaluates extraction accuracy, pack-quantity precision, and token similarity on a 30-case held-out benchmark dataset.

### 3. TabPFN Supplier Risk & Dispute Recovery Intelligence
MarginLeak integrates **TabPFN 2.0** (prior-data fitted networks for tabular data). When analyzing historical supplier behavior:
- TabPFN evaluates past invoice counts, frequency of discrepancies, average error margins, and dispute outcomes.
- It outputs an empirical **Overbilling Risk Score** (`low`, `moderate`, `elevated`) and an estimated **Dispute Win Probability**.
- If historical records are sparse or credentials are absent, the system cleanly degrades to a deterministic statistical median fallback.

### 4. Deterministic Financial Engine
Every dollar calculation uses Python `decimal.Decimal`:
- **Price Variance**: `(Invoice Unit Price - PO Unit Price) × Invoiced Quantity`
- **Quantity Overage**: `(Invoiced Quantity - PO Quantity) × PO Unit Price`
- **Historical Drift**: Compared against the tenant's historical median price for that specific supplier and item.
- Ambiguous matches are marked for review, malformed numeric values are rejected, and duplicate lines are not re-audited as independent exposure.

### 5. Multi-Tenant Enterprise Security
- **Dual-Mode JWT Verification**: Supports modern Supabase asymmetric **`ES256` Elliptic Curve tokens** via Supabase Auth API verification (`/auth/v1/user`), while retaining fast local **`HS256` HMAC verification** when symmetric secrets are configured.
- **TTL Token Caching**: An in-memory cache (`_verified_token_cache`) eliminates redundant round-trips to auth providers during high-frequency API polling.
- **Row-Level Tenancy**: Invoices, purchase orders, reconciliations, and findings are foreign-keyed to `workspace_id`. Cross-tenant record inspection returns strict `404 Not Found` errors.
- **Upload Sandboxing**: Uploaded files use generated UUIDs in restricted directories; directory traversal attacks (`../`) and unauthorized workspace IDs are rejected before parsing.

### 6. Full Technology Stack
- **Frontend**: React 19, TypeScript, Vite, Vanilla CSS design system (dark mode, glassmorphism, responsive cards, micro-animations).
- **Backend**: FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, Pydantic-Settings.
- **Database**: PostgreSQL on Render, SQLite locally.
- **AI & Tabular ML**: Thinking Machines Tinker LoRA (Qwen3-8B), TabPFN 2.0.
- **Deployment**: Docker multi-stage build, Render Blueprint (`render.yaml`).

---

## Why Does Open Innovation Matter?

Accounts-payable auditing should not be a walled-garden monopoly controlled by multi-million-dollar legacy ERP providers. When accounting software operates as an opaque black box:

1. **Trade Secret Confidentiality & Financial Privacy**: Supplier pricing discount agreements, vendor negotiation rates, and wholesale item costs are strictly confidential trade secrets. Businesses cannot legally or commercially stream proprietary supplier invoices into closed commercial LLM servers. Open-weight models can be hosted entirely inside a private VPC or private cloud instance, ensuring zero data leakage.
2. **Domain-Specific Adaptation Over Generalist Chatbots**: Off-the-shelf closed models frequently hallucinate or fail on industrial abbreviations (*"CRG-055 HY BLK TONER"*, *"7P Type C Dock w/ 100W PD"*). Fine-tuning an open-weight model with LoRA on Thinking Machines' Tinker adapts normalization to specific supplier vocabulary without paying massive token fees.
3. **Inspectability & Audit Compliance**: In financial auditing, "trust me" is unacceptable. An open implementation makes the workflow fully inspectable: owners and accountants can see how a product was matched, how an amount was calculated, and which exact source text supported the finding.
4. **Zero Marginal Vendor Tax**: Closed APIs change pricing and deprecate model versions unexpectedly. An open-weight model deployed on open infrastructure gives predictable, fixed marginal costs, making a lean SaaS sustainable from day one.

The most important design choice is not to ask the model to calculate money. Open innovation provides the language interpretation layer, while ordinary deterministic code remains responsible for the numbers and the audit trail.

---

## My Agent Session

This entire application—from backend architecture and Tinker fine-tuning scripts to Supabase authentication debugging, Docker packaging, and UI components—was developed collaboratively with AI agent assistance and recorded via [DevRelay](https://devrelay.com/).

The verified interactive session has been submitted to DEV and can be inspected in full:

* 🔗 **DEV Agent Session**: [https://dev.to/agent_sessions/marginleak-autonomous-accounts-payable-ai-auditor-3800ko](https://dev.to/agent_sessions/marginleak-autonomous-accounts-payable-ai-auditor-3800ko)
* 🆔 **Session ID**: `878`
* 📊 **Scope**: 26 curated, high-value engineering messages (13 deep architectural and ML milestones)

### Interactive Liquid Tag Embeds
The session can be embedded in any DEV community article using DEV's native Liquid tags:

```liquid
{% agent_session 878 %}
```

Or embedded by curated milestone slices:
- **TabPFN Anomaly Scoring & Dispute UI**: `{% agent_session 878 0..2 %}`
- **Render Multi-Stage Docker Packaging**: `{% agent_session 878 3..6 %}`
- **Tinker LoRA Fine-Tuning SDK**: `{% agent_session 878 7..12 %}`
- **Supabase Auth & Workspace Tenancy**: `{% agent_session 878 13..16 %}`
- **Model Loss & Convergence Trajectory**: `{% agent_session 878 17..20 %}`
- **Origin Redirection & DevRelay Registration**: `{% agent_session 878 21..25 %}`

---

## My First User

During development, an early version of MarginLeak was pilot-tested using anonymized order records from a **family-owned hardware and electrical supplies shop** processing roughly 200 invoice lines monthly across 8 recurring suppliers.

### Key Learnings from the Field:
- **Pack Unit Confusion is the #1 Cause of Leaks**: Suppliers frequently bill by the *"inner carton"* (e.g., pack of 12) while purchase orders record individual units. The deterministic regex fallback combined with canonical attribute normalization successfully flagged two separate box-versus-unit pricing mismatches that had previously gone unnoticed.
- **Bookkeepers Want Proof, Not Assertions**: When bookkeepers were shown an AI estimate, they hesitated; when shown the **exact page snippet and arithmetic formula**, they immediately felt comfortable taking action and sending the credit memo request.
- **The Value of One-Click Dispute Letters**: Generating the dispute email draft in the UI reduced the friction of disputing a $35 overcharge from 15 minutes of manual writing to 5 seconds.

*(Note: This was an informal, unpaid testing partnership to refine software usability, not a formal commercial enterprise deployment).*

---

## Prize Categories

### 1. Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle (Primary Track)
MarginLeak is built as a complete, viable, commercial-grade SaaS product addressing a concrete, high-ROI business problem for small businesses and e-commerce sellers. It includes multi-tenant authentication, workspace isolation, evidence-backed reconciliation, automated dispute letter generation, and an interactive hosted demo on Render.

### 2. Best Use of Thinking Machines Tinker ($200)
MarginLeak implements a complete open-weight LoRA fine-tuning workflow with the Tinker SDK, targeting `Qwen/Qwen3-8B` for canonical line-item normalization. The repository contains genuine forward/backward passes, cross-entropy loss computation, optimizer steps, checkpoint export in [train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py), and a 30-case held-out benchmark runner in [run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py).

### 3. Best Use of Render ($200)
MarginLeak is packaged with a multi-stage [Dockerfile](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/Dockerfile) (Node 20 Alpine builder + Python 3.12 slim runtime) and deployed using Infrastructure-as-Code via [render.yaml](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/render.yaml). Render serves the full-stack application, automated PostgreSQL database connection, CORS configuration, and `/health` monitoring.

---

## Additional Information

### Architecture Flowchart

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MARGINLEAK ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Invoice PDF] ──> PyMuPDF Extractor ──> Raw Line Items + Bounding Boxes    │
│  [PO Spreadsheet] ─> Pandas / OpenPyXL ─> Authorized PO Line Items          │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │               CANONICAL NORMALIZATION & MATCHING                    │   │
│   │                                                                     │   │
│   │  • Thinking Machines Tinker LoRA (Qwen3-8B): Canonical attributes   │   │
│   │  • Deterministic Fallback Normalizer: Rule-based regex tokenization │   │
│   │  • RapidFuzz Matcher: Token-sort ratio, SKU alignment, confidence   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │            DETERMINISTIC FINANCIAL RECONCILIATION ENGINE            │   │
│   │                                                                     │   │
│   │  • Exact Python decimal.Decimal precision (zero floating-point err) │   │
│   │  • Price Variance: (Invoice Price - PO Price) × Invoiced Qty        │   │
│   │  • Quantity Variance: (Invoiced Qty - PO Qty) × PO Unit Price       │   │
│   │  • Duplicate Line Detection & Historical Median Price Tracking      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │         TABPFN SUPPLIER RISK & DISPUTE RECOVERY INTELLIGENCE         │   │
│   │                                                                     │   │
│   │  • TabPFN 2.0 Bayesian Tabular Classifier: Supplier Overbilling Risk│   │
│   │  • Dispute Recovery Probability: Historical win rate estimation     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      OUTPUT & REMEDIATION LAYER                     │   │
│   │                                                                     │   │
│   │  • Interactive Audit Dashboard (React 19 + TypeScript + Vite)       │   │
│   │  • PDF Source Snippet & Page Citation                               │   │
│   │  • One-Click Credit-Memo Dispute Generator (Formatted text + mailto)│   │
│   │  • Human-in-the-Loop Feedback: Confirmed corrections saved as aliases│  │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Roadmap & Future Enhancements
- [ ] **Multi-Currency Live FX**: Automated conversion for cross-border supplier invoices using historical European Central Bank (ECB) rates.
- [ ] **Direct Accounting Integrations**: Sync confirmed audit adjustments directly into QuickBooks Online and Xero via OAuth.
- [ ] **Automated Inbox Ingestion**: Webhook listeners to monitor a designated `invoices@company.com` inbox for continuous hands-free reconciliation.
- [ ] **Multi-Model Benchmark Expansion**: Publish full benchmark matrices comparing Tinker LoRA vs Base Qwen3-8B vs Claude/GPT APIs across 500+ real-world invoice formats.

---
*MarginLeak is proudly 100% open-source under the MIT License. Check out the [code on GitHub](https://github.com/inddivyansh/MarginLeak) and try the [live demo](https://marginleak.onrender.com/)!*
