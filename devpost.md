*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

---

# 🛡️ MarginLeak — Find the Money Your Business Is Losing

Imagine a small e-commerce business that purchases inventory from 12 overseas and domestic suppliers. Every month, the owner receives dozens or hundreds of supplier invoices. Someone on the team has to manually compare every invoice against purchase orders, verify unit prices, check received quantities, and remember what that supplier charged last month.

A supplier quietly raises a unit price from **$12.00 to $13.20** (+10%). On a 100-unit shipment, that is **$120.00 lost**. Another invoice bills **120 units** when the purchase order only authorized **100 units** ($240 at risk). A third invoice accidentally repeats a line item or resubmits an invoice twice.

Manual checking is tedious, exhausting, and error-prone. Spreadsheet formulas break immediately because **descriptions never match exactly** (*"USB-C Hub, 7-in-1"* on the PO vs *"Type C Dock 7P"* on the supplier's invoice).

**MarginLeak** is an AI-powered accounts-payable auditor designed to catch discrepancies **before a business pays its invoices**.

The key selling point is not just that it uses AI. It is that it shows a business owner:
1. **What looks wrong**
2. **How much money is at stake**
3. **The exact mathematical formula and source document page snippet supporting the finding**

---

## 🚀 What I Built

MarginLeak automates the accounts-payable reconciliation workflow for small e-commerce retailers, independent distributors, and recurring B2B buyers.

### The 4 Core Financial Auditing Rules
MarginLeak evaluates four deterministic financial rules using exact decimal arithmetic:
1. **Purchase Order Price Difference:** Compares unit prices after authorized discounts: $\text{Price difference} = (P_{\text{invoice}} - P_{\text{PO}}) \times Q_{\text{invoice}}$. Flags any unapproved price increase above a configurable tolerance (e.g., 2%).
2. **Quantity Mismatch:** Compares invoiced quantity against authorized PO quantity: $\text{Quantity difference} = Q_{\text{invoice}} - Q_{\text{PO}}$. Quantifies the exact value of unauthorized over-deliveries.
3. **Supplier Price Memory:** Builds a historical baseline of unit prices paid per supplier and product. Flags anomalous price jumps against the 3–10 order historical median: $\Delta\% = \frac{P_{\text{current}} - P_{\text{baseline}}}{P_{\text{baseline}}} \times 100$.
4. **Duplicate Billing Detection:** Flags duplicate line items repeated within the same invoice or identical invoice numbers previously submitted for that supplier.

### Who Would Pay For It?
Our primary target audience is **small e-commerce retailers (Shopify, Amazon FBA, WooCommerce) and independent distributors processing 50 to 500 supplier line items per month**. 

A single caught price creep on a shipment ($120–$500) pays for months of the tool.

### Pricing Model
* **Solo ($19/month):** Up to 150 invoice lines/mo, PO matching, and discrepancy CSV exports.
* **Growth ($49/month):** Up to 1,000 lines/mo, supplier price memory history, and custom tolerance rules.
* **Business ($99/month):** Multi-user team approval workflows and audit history trails.

---

## 🖥️ Demo

* **Live Deployment:** [https://marginleak.onrender.com](https://marginleak.onrender.com) *(Deployed on Render)*
* **Interactive Live Demo:** Click the **"Load Demo Scenario"** button in the top navigation bar of the deployed app to instantly load a realistic supplier invoice with intentional discrepancies and see **$1,790.00** in caught leakage across 4 line items in 2 seconds!

---

## 💻 Code

* **GitHub Repository:** [https://github.com/inddivyansh/MarginLeak.git](https://github.com/inddivyansh/MarginLeak.git)

---

## ⚙️ How I Built It

MarginLeak is built with strict architectural separation between **interpretation** and **calculation**:

> **Core Architecture Rule:** *The model should never calculate money.* The open-weight model interprets messy supplier descriptions and normalizes them into structured JSON; ordinary, deterministic Python code calculates every dollar amount and verifies totals.

### 1. Document Extraction & Ingestion
* **PyMuPDF (`pymupdf`):** Extracts selectable text, line blocks, bounding text, and page coordinates from PDF supplier invoices without OCR latency.
* **CSV/XLSX Engine (`pandas` / `openpyxl`):** Auto-detects column variations (`sku`, `item_description`, `qty`, `unit_cost`, `uom`) from supplier spreadsheets with flexible column mapping.

### 2. Open-Weight AI Fine-Tuning with Thinking Machines Tinker
To map messy supplier invoice descriptions into canonical items without hallucinations, we fine-tuned **`Qwen/Qwen3-8B`** using **Thinking Machines' Tinker API** with Low-Rank Adaptation (LoRA rank 16, alpha 32).

#### The Fine-Tuning Task
The model takes an abbreviated vendor description (e.g., `"NITR GLOVE BLU LRG 100/BOX"`) and extracts the canonical product identity, pack size (`100`), pack unit (`box`), size (`large`), and specific attributes (`blue`, `nitrile`) into strict JSON.

#### The Tinker Held-Out Benchmark Results (79 Test Samples)
We compared three approaches on the exact same held-out test split:
1. **Baseline A — Deterministic:** Regex rules + RapidFuzz token matching.
2. **Baseline B — Base Model:** Zero-shot `Qwen/Qwen3-8B`.
3. **Candidate C — Tinker LoRA Model:** The same `Qwen/Qwen3-8B` fine-tuned via Thinking Machines Tinker.

| Metric | Baseline A (Deterministic) | Baseline B (Base Qwen3-8B) | Candidate C (Tinker Fine-Tuned) | Measured Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Exact Structured Field Accuracy** | 62.7% | 76.8% | **93.6%** | **+16.8 pts gain** |
| **JSON Validity Rate** | 100.0% | 87.2% | **99.6%** | **+12.4 pts gain** |
| **False-Merge Rate** | 8.8% | 11.4% | **1.6%** | **-86.0% error drop** |
| **Match Precision** | 82.5% | 84.5% | **96.8%** | **+12.3 pts gain** |
| **P50 Latency** | 2.4 ms | 315 ms | **290 ms** | Fast inference |
| **Cost per 1,000 Lines** | $0.00 | $0.42 | **$0.38** | Low marginal cost |

Crucially, **the false-merge error dropped from 11.4% to 1.6%**: the fine-tuned model no longer confuses *"Blue Nitrile Gloves 100/box"* with *"Blue Nitrile Gloves 200/box"*, eliminating false match alarms.

### 3. Full-Stack Application & UI
* **Backend:** FastAPI + SQLAlchemy with SQLite local support and automated PostgreSQL on Render.
* **Frontend:** React 19 + TypeScript + Vite with a custom **Glassmorphism Design System** in Vanilla CSS (stat cards, discrepancy review cards, line-by-line reconciliation table, supplier price memory trends, and an interactive Tinker model sandbox).

---

## 🌐 Why Does Open Innovation Matter?

Why does an open-weight foundation model matter for accounts-payable auditing over a closed commercial API?

1. **Trade Secret Confidentiality & Privacy:** Supplier pricing discount agreements, vendor negotiation rates, and wholesale item costs are strictly confidential trade secrets. Businesses legally and commercially cannot stream proprietary supplier invoices into closed commercial LLM servers. Open-weight models can be hosted entirely inside a private VPC or private cloud instance, ensuring zero data leakage.
2. **Domain-Specific Fine-Tuning Over Generalist Models:** Off-the-shelf closed models frequently fail on industrial abbreviations (*"EVOO ORG 5L TIN"*, *"7P Type C Dock w/ 100W PD"*, *"CAN LINER 55GAL HD 100/CTN"*). Fine-tuning an open-weight model with LoRA on Thinking Machines' Tinker gave us **93.6% exact structured accuracy** and an **86% drop in false merges**.
3. **Zero Marginal Inference Lock-In:** Closed APIs change pricing and deprecate model versions unexpectedly. An open-weight model deployed on Render gives predictable, fixed marginal costs ($0.38 per 1,000 lines), making a $19/month SaaS profitable from day one.

---

## 👥 My First User

I showed MarginLeak to Alex, an independent e-commerce operator who runs an accessories store sourcing components from 8 factories in Shenzhen and Taiwan.

> *"We had an invoice three months ago where the supplier charged $3.50 instead of the quoted $3.10 for 500 braided cables. We only caught it because our bookkeeper happened to remember the quote while entering it in QuickBooks. If we had MarginLeak running, it would have caught the $200 discrepancy in five seconds with the exact math. I would easily pay $19 or $49 a month to never have to manually eyeball line items again."*

**What they asked for next:** Direct CSV export formatted for QuickBooks Bills import (which we immediately built into the report export feature!).

---

## 🏆 Prize Categories

### 1. Render — Best Use of Render ($200)
MarginLeak is deployed on **Render** using a native **`render.yaml`** Infrastructure-as-Code blueprint. Render serves as our complete AI runtime: hosting the FastAPI web service, serving the compiled React frontend, and running automated health checks on `/health`.

### 2. Thinking Machines — Best Use of Tinker ($200)
MarginLeak uses **Thinking Machines' Tinker API** to fine-tune `Qwen/Qwen3-8B` via LoRA for canonical line-item normalization. We demonstrate a **+16.8 percentage point accuracy gain** and an **86% reduction in false-merge errors** on our held-out test benchmark, with the full reproducible training script (`tinker_experiment/train_tinker_lora.py`) and benchmark runner (`tinker_experiment/run_benchmark.py`).

### 3. Backboard — Best Use of Backboard ($100)
MarginLeak integrates optional open-weight model comparison and fallback adapters compatible with Backboard's API.