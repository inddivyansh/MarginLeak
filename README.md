# MarginLeak: Find the Money Your Business Is Losing

> Autonomous accounts-payable AI auditor for small businesses and e-commerce sellers.
> Built for the Hacktoberfest 2026 AI Challenge: Side Hustle.

[![Render](https://img.shields.io/badge/Deploy-Render-blue?logo=render)](https://render.com)
[![Thinking Machines](https://img.shields.io/badge/Fine--Tuned-Thinking%20Machines%20Tinker-indigo)](https://tinker-docs.thinkingmachines.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev)

---

## The Problem: Unnoticed Accounts-Payable Leakage

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

## Key Differentiators

| Feature | How MarginLeak Solves It |
| :--- | :--- |
| **Fuzzy Matching with Evidence** | Understands that *"Type C Dock 7P"* and *"USB-C Hub 7-in-1"* represent the same item without silently guessing on ambiguous pack sizes (e.g., box of 100 vs box of 200). |
| **Supplier Price Memory** | Retains a historical memory of unit prices paid per supplier and product. Flags unexplained increases over baseline median prices. |
| **Deterministic Financial Rules** | **The LLM never calculates money.** Open-weight models normalize messy descriptions, while deterministic Python code with `decimal.Decimal` calculates exact price and quantity variances. |
| **Human Review & Learning** | Reviewers can confirm, dismiss, or correct matches. Approved corrections are saved as supplier aliases to improve future reconciliations automatically. |

---

## Open-Weight Fine-Tuning with Thinking Machines Tinker

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

### Held-Out Benchmarking

The benchmark runner measures the deterministic fallback locally and evaluates base and LoRA models only when real Tinker model artifacts are supplied. It writes measured results to `tinker_experiment/benchmark_results.json`; unavailable model metrics are recorded as `not_run`, never estimated.

Run the deterministic report:

```bash
python tinker_experiment/run_benchmark.py
```

After training and saving a Tinker sampler artifact, pass `--base-model`, `--tinker-model-path`, and `TINKER_API_KEY` to measure model comparisons. The repository does not claim base-model or LoRA metrics until those real inference runs have been completed.

To run real LoRA training:

```bash
set TINKER_API_KEY=your_key_here
python tinker_experiment/train_tinker_lora.py --epochs 2 --lora-rank 16
```

The trainer calls Tinker's `create_lora_training_client`, performs `forward_backward` and optimizer steps, saves a sampler artifact, and records the returned checkpoint metadata in `tinker_experiment/checkpoint_metadata.json`. Without `TINKER_API_KEY`, it exits with an error instead of simulating training.

---

## System Architecture

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

## Quickstart: Running Locally

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

# Optional: edit .env to configure the database and AI credentials.
# TINKER_API_KEY enables Tinker normalization; blank uses the deterministic fallback.

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

Click **"Load Demo Scenario"** in the top bar to seed realistic supplier invoices and inspect the reconciliation workflow.

## API Surface

All API routes are mounted under `/api/v1`.

| Area | Routes |
| :--- | :--- |
| Documents | `POST /documents/invoices`, `POST /purchase-orders/import`, `POST /purchase-orders/confirm-import` |
| Reconciliation | `POST /reconciliations`, `GET /reconciliations`, `GET /reconciliations/{id}`, `PATCH /findings/{id}` |
| Evidence and actions | `GET /findings/{id}/dispute-draft`, `GET /reports/{reconciliation_id}.csv`, `PATCH /line-matches/{id}` |
| Risk and history | `GET /supplier-risk`, `GET /history/prices` |
| Demo and evaluation | `POST /demo/seed-sample-scenario`, `POST /evaluations/normalize-test`, `GET /evaluations/latest` |

Financial values are parsed and calculated with `decimal.Decimal`. Malformed numeric input returns a validation error, ambiguous product matches remain review-only, and uploaded files are stored under generated names rather than user-controlled paths.

---

## Deploying to Render

MarginLeak includes a ready-to-use **`render.yaml`** blueprint for one-click deployment.

1. Fork or push this repository to GitHub: `https://github.com/inddivyansh/MarginLeak.git`
2. Log in to your [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint** and connect your GitHub repository.
4. Render will automatically build the React frontend and deploy the FastAPI web service!
5. Add your environment variables:
  * `TINKER_API_KEY`: Thinking Machines Tinker API key, optional because the deterministic fallback remains available
  * `BACKBOARD_API_KEY`: Optional Backboard integration key
  * `TABPFN_ENABLED`: Set to `true` only when the image includes `backend/requirements-tabpfn.txt`
  * `ENVIRONMENT`: `production`

The Render blueprint uses the included Dockerfile and provisions a persistent PostgreSQL database. TabPFN remains disabled by default so the standard deployment stays lightweight; install `backend/requirements-tabpfn.txt` in a custom image when enabling it.

---

## Running the Tinker Benchmark

To reproduce the model benchmark:
```bash
# 1. Generate dataset splits
python tinker_experiment/dataset_generator.py

# 2. Run real LoRA training smoke test; requires TINKER_API_KEY
python tinker_experiment/train_tinker_lora.py --smoke-test

# 3. Evaluate held-out benchmark; model metrics require real Tinker artifacts
python tinker_experiment/run_benchmark.py
```

---

## License
MIT License. Built for Hacktoberfest 2026.
