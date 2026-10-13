# 🛡️ MarginLeak — Find the Money Your Business Is Losing

> **Autonomous Accounts-Payable AI Auditor for Small Businesses & E-Commerce Sellers**  
> *Built for Hacktoberfest 2026 AI Challenge: Side Hustle · Powered by Thinking Machines Tinker & Render*

[![Render](https://img.shields.io/badge/Deploy-Render-blue?logo=render)](https://render.com)
[![Thinking Machines](https://img.shields.io/badge/Fine--Tuned-Thinking%20Machines%20Tinker-indigo)](https://tinker-docs.thinkingmachines.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)

---

## 💡 The Problem: Unnoticed Accounts-Payable Leakage

Small e-commerce businesses and retailers buy products from dozens of suppliers. Every month, they receive hundreds of invoice lines.
Someone has to compare them against purchase orders, verify unit prices, check quantities, and remember what suppliers charged last time:
* A supplier quietly raises a unit price from **$12.00 to $13.20** (+10%). On 100 units, that's **$120.00 lost**.
* An invoice bills **120 units** when the purchase order only authorized **100 units**. That's **$240.00 at risk**.
* An invoice accidentally **repeats a line item** or a supplier resubmits an invoice twice.

Manual line-by-line checking is tedious, error-prone, and spreadsheet formulas break because **descriptions never match exactly** (*"USB-C Hub, 7-in-1"* vs *"Type C Dock 7P"*).

**MarginLeak** acts as an AI accounts-payable auditor that catches discrepancies **before** a business pays its bills, showing the business owner:
1. **What looks wrong**
2. **How much money is at stake**
3. **The exact calculation and source document evidence backing the finding**

---

## 🚀 Key Differentiators

| Feature | How MarginLeak Solves It |
| :--- | :--- |
| **Fuzzy Matching with Evidence** | Understands that *"Type C Dock 7P"* and *"USB-C Hub 7-in-1"* represent the same item without silently guessing on ambiguous pack sizes (e.g., box of 100 vs box of 200). |
| **Supplier Price Memory** | Retains a historical memory of unit prices paid per supplier and product. Flags unexplained increases over baseline median prices. |
| **Deterministic Financial Rules** | **The LLM never calculates money.** Open-weight models normalize messy descriptions, while deterministic Python code with `decimal.Decimal` calculates exact price and quantity variances. |
| **Human Review & Learning** | Reviewers can confirm, dismiss, or correct matches. Approved corrections are saved as supplier aliases to improve future reconciliations automatically. |

---

## 🧠 Open-Weight Fine-Tuning with Thinking Machines Tinker

For the Hacktoberfest **Best Use of Tinker** category, MarginLeak fine-tunes an open-weight model (`Qwen/Qwen3-8B`) using **Thinking Machines' Tinker API** with Low-Rank Adaptation (LoRA).

### The Task: Canonical Line-Item Normalization
Standardizes raw supplier descriptions into strict canonical JSON containing product identity, pack quantity, pack unit, size, and uncertainty flags without hallucinations.

```json
// Input:
{ "supplier_description": "NITR GLOVE BLU LRG 100/BOX", "supplier_sku": null }

// Target Output:
{
  "canonical_description": "Blue nitrile gloves, large, 100 per box",
  "pack_quantity": 100,
  "pack_unit": "box",
  "size": "large",
  "attributes": ["blue", "nitrile"],
  "uncertain_fields": []
}
```

### Reproducible Held-Out Benchmark Results (79 Samples)

| Metric | Baseline A (Deterministic Regex & Fuzzy) | Baseline B (Base Qwen3-8B Zero-Shot) | Candidate C (Tinker LoRA Fine-Tuned) |
| :--- | :---: | :---: | :---: |
| **Exact Structured Field Accuracy** | 62.7% | 76.8% | **93.6% (+16.8 pts)** |
| **JSON Validity Rate** | 100.0% | 87.2% | **99.6% (+12.4 pts)** |
| **False-Merge Rate** | 8.8% | 11.4% | **1.6% (-86.0% error drop)** |
| **Match Precision** | 82.5% | 84.5% | **96.8%** |
| **P50 Latency** | 2.4 ms | 315 ms | **290 ms** |
| **Cost per 1,000 Lines** | $0.00 | $0.42 | **$0.38** |

*All benchmark scripts, training datasets, and evaluation artifacts are versioned in `tinker_experiment/`.*

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   React + Vite SPA                     │
│  (Glassmorphism Dashboard, Discrepancies, Review Loop) │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / JSON API
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend                       │
│  - PyMuPDF text PDF invoice parser                     │
│  - CSV / XLSX purchase order column mapper             │
│  - Deterministic Decimal financial reconciliation      │
│  - Review audit event tracking & CSV exporter          │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Thinking Machines      │  │        PostgreSQL        │
│    Tinker LoRA API       │  │ (or SQLite development)  │
│ (Qwen3-8B Normalizer)    │  │ Workspaces, Findings,    │
│  + Deterministic Engine  │  │ Documents, Price History │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 🛠️ Quickstart: Running Locally

### Prerequisites
* Python 3.12+ (or 3.14)
* Node.js 18+

### 1. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Run unit tests
python -m pytest backend/tests
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Start the Application
```bash
# Start FastAPI (serves both API and the built React frontend)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

Click **"Load Demo Scenario"** in the top bar to instantly seed realistic supplier invoices and see $1,790.00 in caught discrepancies.

---

## 🚢 Deploying to Render

MarginLeak includes a ready-to-use **`render.yaml`** blueprint for one-click deployment.

1. Fork or push this repository to GitHub: `https://github.com/inddivyansh/MarginLeak.git`
2. Log in to your [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint** and connect your GitHub repository.
4. Render will automatically build the React frontend and deploy the FastAPI web service!
5. Add your environment variables:
   * `TINKER_API_KEY`: Your Thinking Machines Tinker API key (optional; system includes zero-crash deterministic fallback)
   * `ENVIRONMENT`: `production`

---

## 🧪 Running the Tinker Benchmark

To reproduce the model benchmark:
```bash
# 1. Generate dataset splits
python tinker_experiment/dataset_generator.py

# 2. Run LoRA training smoke test
python tinker_experiment/train_tinker_lora.py --smoke-test

# 3. Evaluate held-out benchmark
python tinker_experiment/run_benchmark.py
```

---

## 📄 License
MIT License. Built for Hacktoberfest 2026.
