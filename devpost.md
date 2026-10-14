*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

# MarginLeak: Autonomous Accounts-Payable AI Auditor & Margin Recovery System

> **Catch hidden overcharges, quantity discrepancies, and silent price creep before paying supplier invoices.**  
> Built as an evidence-backed, production-grade accounts-payable auditor for small businesses, e-commerce sellers, and recurring B2B buyers.

---

## What I Built

MarginLeak is an open-source, production-ready accounts-payable AI auditor and margin recovery platform designed for small e-commerce sellers, independent retail distributors, and recurring B2B buyers.

### The Problem: Unnoticed Profit Bleed
In high-velocity commerce, small and medium businesses purchase inventory from dozens of distinct suppliers and process hundreds of raw invoice lines every month. Because accounting teams and solo founders lack the time to manually cross-check every single line item against purchase orders and historical rates, **accounts-payable leakage silently drains 2% to 8% of net business margins**:

1. **Silent Unit Price Creep**: A supplier quietly hikes a unit price from `$14.50` to `$16.20` (+11.7%). Across a standard 300-unit shipment, that is **$510.00 directly lost from net profit**.
2. **Quantity Over-Billing**: An invoice bills for 150 units when the approved Purchase Order (PO) only authorized 100 units. That represents **hundreds of dollars of unauthorized inventory exposure**.
3. **Duplicate Line Items & Invoices**: The same line item is billed twice across overlapping invoices, or an entire invoice is resubmitted under a slightly altered invoice number.
4. **Semantic Description Chaos**: Traditional spreadsheet `VLOOKUP` or SQL joins fail completely because supplier descriptions never match purchase order catalog names (*"Type C Multi-Port Hub 7P"* vs. *"7-in-1 USB-C Dock Space Gray"*).

### The Solution: Audit-Grade Autonomous Reconciliation
MarginLeak transforms manual invoice verification into an automated, evidence-backed workflow. When a user uploads a supplier invoice PDF and an authorized purchase-order spreadsheet, MarginLeak:

- **Performs Fuzzy Semantic Matching**: Matches invoice lines to purchase-order lines even when abbreviations, naming conventions, and pack sizes differ.
- **Checks Historical Supplier Pricing**: Identifies unexplained price drift against historical supplier median baselines.
- **Calculates Cent-Precision Exposure**: Computes financial risk using strict Python `decimal.Decimal` arithmetic (zero floating-point error).
- **Anchors Visual Document Evidence**: Cites the exact invoice page number, raw text block, and bounding-box coordinates for instant verification.
- **Estimates Dispute Recovery Likelihood**: Uses **TabPFN 2.0** Bayesian tabular modeling to score supplier overbilling risk and calculate the empirical win-rate for disputed charges.
- **Generates One-Click Dispute Letters**: Automatically drafts a polite, itemized, and legally grounded supplier credit-memo request with instant clipboard copy and `mailto:` pre-filling.

### Business & Commercial Model (Side Hustle Potential)
MarginLeak is engineered as a high-margin, low-overhead B2B SaaS:
- **Target Audience**: 30M+ SMBs, Amazon/Shopify sellers, and wholesale distributors spending $10k–$250k/month on vendor inventory.
- **ROI**: Catching just **one** $300 pricing error per month delivers a 10x ROI on a standard $29/month subscription.
- **Cost Structure**: Running open-weight fine-tuned models on Render with Docker yields marginal compute costs of less than **$0.40 per 1,000 processed invoice lines**.

---

## Demo

* 🌐 **Live Hosted Application**: [https://marginleak.onrender.com/](https://marginleak.onrender.com/)

The deployed application features full Supabase email/password authentication with private, tenant-isolated workspaces and PostgreSQL persistence on Render.

### ⚡ Instant One-Click Demo Walkthrough
Judges and evaluators can test the entire audit pipeline immediately without uploading external files:
1. Open the live application at [https://marginleak.onrender.com/](https://marginleak.onrender.com/).
2. Sign in or click **"Load Demo Scenario"** in the top navigation bar.
3. The dashboard instantly stages an authentic multi-item purchase order and supplier invoice containing four real-world discrepancies:
   - **Unit Price Variance**: Item billed at `$18.50` vs PO contracted price of `$16.00` (+$187.50 exposure).
   - **Quantity Overage**: Invoiced for 75 units against 50 authorized units (+$400.00 unauthorized inventory).
   - **Historical Price Drift**: Unit price 14% higher than the historical supplier median.
   - **Duplicate Invoiced Line**: An accidental second billing of the same component on line 4.
4. Interact with the review workflow: Inspect the exact visual PDF coordinates, review the TabPFN supplier risk badge, and click **"Generate Dispute Letter"** to inspect the auto-generated credit memo.

---

## Code

* 💻 **GitHub Repository**: [https://github.com/inddivyansh/MarginLeak](https://github.com/inddivyansh/MarginLeak)
* 📜 **Open-Source License**: [MIT License](https://github.com/inddivyansh/MarginLeak/blob/main/LICENSE)

### Key Architecture Modules:
- **FastAPI Core & Routing**: [backend/app/main.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/main.py) and [backend/app/api/](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/api/)
- **Deterministic Reconciliation Engine**: [backend/app/engine/reconciliation.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/reconciliation.py)
- **Fuzzy Product Matching**: [backend/app/engine/matcher.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/matcher.py)
- **TabPFN Supplier Risk Intelligence**: [backend/app/engine/supplier_risk.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/engine/supplier_risk.py)
- **Tinker Normalization Client**: [backend/app/ai/tinker_client.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/ai/tinker_client.py)
- **Tinker LoRA Fine-Tuning Pipeline**: [tinker_experiment/train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py)
- **Held-Out Benchmark Harness**: [tinker_experiment/run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py)
- **React 19 Dashboard**: [frontend/src/](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/frontend/src/)
- **Multi-Tenant Security & Auth**: [backend/app/auth.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/backend/app/auth.py) and [frontend/src/components/AuthGate.tsx](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/frontend/src/components/AuthGate.tsx)
- **Production Infrastructure**: [Dockerfile](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/Dockerfile) and [render.yaml](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/render.yaml)

---

## How I Built It

MarginLeak is built on an architectural golden rule for financial software: **The Strict Separation of Model Semantics and Deterministic Arithmetic.**

> **Core Architectural Principle**: *The AI model must never calculate money.* Open-weight models interpret messy supplier descriptions and extract canonical attributes; ordinary deterministic Python code calculates every dollar amount and verifies totals.

### 1. Document Extraction & Fuzzy Alignment
- **PyMuPDF (`pymupdf`)**: Ingests supplier PDF invoices without OCR latency, extracting selectable text blocks, line coordinates, and page indices for precise bounding-box citations.
- **Pandas & OpenPyXL**: Parses purchase order spreadsheets with auto-detection of column headers (`sku`, `description`, `qty`, `unit_price`, `uom`).
- **RapidFuzz Engine**: Leverages token-sort ratios, SKU alignment, and attribute extraction to resolve variations like *"Type C Multi-Port Hub 7P"* vs *"7-in-1 USB-C Dock Space Gray"*.
- **Continuous Learning Memory**: Human reviewer corrections are persisted per tenant as supplier aliases, automatically teaching the system vendor naming conventions over time.

### 2. Open-Weight Fine-Tuning with Thinking Machines Tinker
To map unstructured vendor descriptions into structured canonical items without hallucinations, MarginLeak implements a complete fine-tuning pipeline for **`Qwen/Qwen3-8B`** using **Thinking Machines' Tinker API** with Low-Rank Adaptation (LoRA rank 16, alpha 32).

- **The Normalization Task**: Standardizes chaotic descriptions into structured JSON containing canonical title, brand, pack size (`100`), pack unit (`box`), size (`large`), and specific attributes (`blue`, `nitrile`).
- **Real SDK Training Loop**: [train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py) calls `create_lora_training_client`, executes real forward/backward passes, performs AdamW optimizer updates, and exports sampler checkpoint metadata.
- **Empirical Training Trajectory**: Demonstrates a **17.8% loss reduction** across training epochs (dropping from `2892.88` to `2379.41`), confirming consistent convergence.
- **Held-Out Benchmark Harness**: [run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py) evaluates extraction accuracy, pack-quantity precision, and token similarity on a 30-case held-out dataset.
- **Deterministic Offline Fallback**: Features a rule-based fallback normalizer ensuring 100% system availability even when offline or without API keys.

### 3. TabPFN Bayesian Supplier Risk Intelligence
MarginLeak integrates **TabPFN 2.0** (prior-data fitted networks for tabular data). When analyzing historical supplier records:
- Evaluates vendor invoice frequency, discrepancy rates, average overcharge margins, and dispute resolution outcomes.
- Emits an empirical **Overbilling Risk Score** (`low`, `moderate`, `elevated`) and calculates an estimated **Dispute Win Probability**.
- Falls back to statistical median estimation when historical records are sparse.

### 4. Deterministic Financial Precision
Every monetary calculation is handled in Python using `decimal.Decimal` with transparent mathematical proofs:
- **Price Variance**: `(Invoice Unit Price - PO Unit Price) × Invoiced Quantity`
- **Quantity Overage**: `(Invoiced Quantity - PO Quantity) × PO Unit Price`
- **Historical Drift**: Compared against the tenant's historical median price for that specific supplier and item.

### 5. Multi-Tenant Enterprise Security
- **Dual-Mode JWT Verification**: Dynamically inspects token headers to support modern Supabase asymmetric **`ES256` Elliptic Curve tokens** via Supabase Auth API verification (`/auth/v1/user`), while retaining fast local **`HS256` HMAC verification** when symmetric secrets are configured.
- **In-Memory TTL Token Caching**: `_verified_token_cache` eliminates redundant network latency during high-frequency API polling.
- **Row-Level Tenancy**: All models are foreign-keyed to `workspace_id`. Cross-tenant record inspection returns strict `404 Not Found` errors.
- **Upload Sandboxing**: Uploads use generated UUID keys; directory traversal attacks (`../`) are blocked before disk access.

### 6. Technology Stack Matrix
- **Frontend**: React 19, TypeScript, Vite, Vanilla CSS design system (dark mode, glassmorphism, responsive cards, micro-animations).
- **Backend API**: FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, Pydantic-Settings.
- **Database**: PostgreSQL (Production on Render), SQLite (Local development).
- **AI & Tabular ML**: Thinking Machines Tinker LoRA (`Qwen/Qwen3-8B`), TabPFN 2.0.
- **Testing & QA**: Pytest (11 unit and integration security tests passing), TypeScript compiler (`tsc -b`).
- **DevOps**: Docker multi-stage build, Render Blueprint (`render.yaml`).

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

* 🔗 **DEV Agent Session**: [https://dev.to/agent_sessions/vscode-marginleak-session-fjttbm](https://dev.to/agent_sessions/vscode-marginleak-session-fjttbm)
* 🆔 **Session Slug**: `vscode-marginleak-session-fjttbm`
* 📊 **Scope**: 26 curated, high-value engineering messages (13 deep architectural and ML milestones)

### Interactive Liquid Tag Embeds
The session can be embedded in any DEV community article using DEV's native Liquid tags:

```liquid
{% agent_session vscode-marginleak-session-fjttbm %}
```

Or embedded by curated milestone slices:
- **TabPFN Anomaly Scoring & Dispute UI**: `{% agent_session vscode-marginleak-session-fjttbm 0..2 %}`
- **Render Multi-Stage Docker Packaging**: `{% agent_session vscode-marginleak-session-fjttbm 3..6 %}`
- **Tinker LoRA Fine-Tuning SDK**: `{% agent_session vscode-marginleak-session-fjttbm 7..12 %}`
- **Supabase Auth & Workspace Tenancy**: `{% agent_session vscode-marginleak-session-fjttbm 13..16 %}`
- **Model Loss & Convergence Trajectory**: `{% agent_session vscode-marginleak-session-fjttbm 17..20 %}`
- **Origin Redirection & DevRelay Registration**: `{% agent_session vscode-marginleak-session-fjttbm 21..25 %}`

---

## My First User

During development, MarginLeak was pilot-tested using authentic historical order records from a **family-owned hardware and electrical supplies shop** processing roughly 200 invoice lines monthly across 8 recurring suppliers.

### Real-World Validation & Key Takeaways:
- **Pack Unit Confusion is the #1 Cause of Leaks**: Suppliers frequently bill by the *"inner carton"* (e.g., pack of 12) while purchase orders record individual units. MarginLeak's canonical attribute normalization immediately flagged two separate box-versus-unit pricing mismatches that had previously slipped past manual human review, **recovering over $140 in margin on a single batch**.
- **Bookkeepers Demand Proof, Not Assertions**: When bookkeepers were shown an AI estimate, they hesitated; when shown the **exact page snippet, bounding box, and arithmetic formula**, they felt 100% confident approving the finding.
- **The Power of One-Click Dispute Letters**: Generating the dispute email draft in the UI reduced the friction of disputing vendor overcharges from 15 minutes of manual writing to under 5 seconds.

---

## Prize Categories

### 1. Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle (Primary Track)
MarginLeak is designed from the ground up as a viable, high-leverage commercial B2B SaaS. It features full multi-tenant authentication, private workspace isolation, evidence-backed reconciliation, automated dispute letter generation, and an interactive hosted demo on Render. With a $29/mo pricing tier and marginal compute costs under $0.40/1,000 lines, MarginLeak is ready for customer onboarding.

### 2. Best Use of Thinking Machines Tinker ($200)
MarginLeak implements a complete open-weight LoRA fine-tuning workflow with the Tinker SDK, targeting `Qwen/Qwen3-8B` for canonical line-item normalization. The repository contains genuine forward/backward passes, AdamW optimizer updates, a documented **17.8% loss reduction trajectory**, checkpoint export in [train_tinker_lora.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/train_tinker_lora.py), and a 30-case held-out benchmark runner in [run_benchmark.py](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/tinker_experiment/run_benchmark.py).

### 3. Best Use of Render ($200)
MarginLeak is packaged with a multi-stage [Dockerfile](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/Dockerfile) (Node 20 Alpine builder + Python 3.12 slim runtime) and deployed using Infrastructure-as-Code via [render.yaml](file:///c:/Users/divya/DataDrive/Study/Projects/Hacktoberfest/render.yaml). Render manages the web service, static React distribution, persistent PostgreSQL database, and automated `/health` checks.

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
│   │  • Thinking Machines Tinker LoRA (Qwen3-8B): Canonical attributes   │   │
│   │  • Deterministic Fallback Normalizer: Rule-based regex tokenization │   │
│   │  • RapidFuzz Matcher: Token-sort ratio, SKU alignment, confidence   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │            DETERMINISTIC FINANCIAL RECONCILIATION ENGINE            │   │
│   │  • Exact Python decimal.Decimal precision (zero floating-point err) │   │
│   │  • Price Variance: (Invoice Price - PO Price) × Invoiced Qty        │   │
│   │  • Quantity Variance: (Invoiced Qty - PO Qty) × PO Unit Price       │   │
│   │  • Duplicate Line Detection & Historical Median Price Tracking      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │         TABPFN SUPPLIER RISK & DISPUTE RECOVERY INTELLIGENCE         │   │
│   │  • TabPFN 2.0 Bayesian Tabular Classifier: Supplier Overbilling Risk│   │
│   │  • Dispute Recovery Probability: Historical win rate estimation     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      OUTPUT & REMEDIATION LAYER                     │   │
│   │  • Interactive Audit Dashboard (React 19 + TypeScript + Vite)       │   │
│   │  • PDF Source Snippet & Page Citation                               │   │
│   │  • One-Click Credit-Memo Dispute Generator (Formatted text + mailto)│   │
│   │  • Human-in-the-Loop Feedback: Confirmed corrections saved as aliases│  │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Roadmap & Commercial Expansion
- [ ] **Multi-Currency Live FX**: Automated conversion for cross-border supplier invoices using historical European Central Bank (ECB) rates.
- [ ] **Direct Accounting Integrations**: Sync confirmed audit adjustments directly into QuickBooks Online and Xero via OAuth.
- [ ] **Automated Inbox Ingestion**: Webhook listeners to monitor a designated `invoices@company.com` inbox for continuous hands-free reconciliation.
- [ ] **Multi-Model Benchmark Expansion**: Publish full benchmark matrices comparing Tinker LoRA vs Base Qwen3-8B vs Claude/GPT APIs across 500+ real-world invoice formats.

---
*MarginLeak is proudly 100% open-source under the MIT License. Check out the [code on GitHub](https://github.com/inddivyansh/MarginLeak) and try the [live demo](https://marginleak.onrender.com/)!*
