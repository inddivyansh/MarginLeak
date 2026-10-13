*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built

MarginLeak is an open-source accounts-payable auditor for small e-commerce sellers, independent distributors, and recurring B2B buyers.

Small businesses receive invoices from many suppliers and often compare them manually against purchase orders and past prices. That makes it easy to miss a quiet price increase, an over-billed quantity, a duplicate line, or a duplicate invoice. MarginLeak turns that review into an evidence-backed workflow.

A user can upload a supplier invoice PDF and a purchase order spreadsheet. MarginLeak matches invoice lines to purchase-order lines even when descriptions differ, checks historical supplier pricing, and presents findings with:

- The discrepancy type and severity
- The amount at risk
- The deterministic calculation formula
- The invoice page and source-text snippet
- A review workflow for confirming, dismissing, resolving, or correcting findings
- A generated supplier credit-memo request for confirmed findings
- A supplier overbilling-risk and dispute-win estimate based on historical records

The primary customer is a small business owner or bookkeeper processing roughly 50 to 500 invoice lines per month. The product is designed as a focused accounts-payable SaaS rather than a general-purpose enterprise procurement suite.

## Demo

Public hosted demo: https://marginleak.onrender.com/

The deployed application opens with Supabase email/password authentication. After signing in, each account receives a private workspace. The dashboard includes a one-click demo scenario that seeds a purchase order and supplier invoice with intentional price, quantity, historical-price, and duplicate-line findings.


## Code

GitHub repository: https://github.com/inddivyansh/MarginLeak

The repository includes a one-click demo scenario in the dashboard. It seeds a realistic supplier purchase order and invoice with price, quantity, historical-price, and duplicate-line discrepancies.

Important implementation areas:

- Backend API: `backend/app/main.py` and `backend/app/api/`
- Deterministic reconciliation: `backend/app/engine/reconciliation.py`
- Product matching: `backend/app/engine/matcher.py`
- Tinker normalization client: `backend/app/ai/tinker_client.py`
- Tinker training: `tinker_experiment/train_tinker_lora.py`
- Held-out evaluation: `tinker_experiment/run_benchmark.py`
- React dashboard: `frontend/src/`
- Render deployment: `render.yaml` and `Dockerfile`
- Authentication and workspace ownership: `backend/app/auth.py`, `backend/app/api/auth.py`, and `frontend/src/components/AuthGate.tsx`

The project is licensed under the MIT License.

## How I Built It

MarginLeak uses a strict separation between model interpretation and financial computation.

The open-weight model is responsible for interpreting messy supplier descriptions. The intended fine-tuning workflow uses Qwen3-8B with Thinking Machines Tinker LoRA supervised fine-tuning. The Tinker trainer now uses the SDK's real LoRA training client, forward/backward passes, optimizer steps, and sampler checkpoint export. It requires `TINKER_API_KEY` and exits instead of simulating training when the key is absent.

The application also has a deterministic fallback normalizer so the core product works without an AI credential. This fallback is useful for local development and keeps document reconciliation available when model inference is unavailable.

The financial engine never delegates money calculations to a model. It uses Python `decimal.Decimal` for price variance, quantity overage, historical median comparisons, and exposure values. Ambiguous matches are review-only, malformed numeric values are rejected, and duplicate lines are not re-audited as independent exposure.

The rest of the stack is:

- FastAPI and SQLAlchemy for the backend API and persistence
- SQLite locally and PostgreSQL on Render
- PyMuPDF for text-based invoice PDFs
- Pandas and OpenPyXL for purchase-order spreadsheets
- RapidFuzz and deterministic matching rules for product reconciliation
- React 19, Vite, and TypeScript for the dashboard
- Docker for the production image

The benchmark runner evaluates the deterministic fallback locally. Base-model and LoRA metrics are recorded as `not_run` until real Tinker model artifacts and inference runs are supplied. This keeps the repository from presenting estimated metrics as measured results.

For deployment, Supabase Auth handles email/password identity and session restoration. FastAPI verifies the Supabase access token, maps it to a local user record, creates a private workspace on first authenticated access, and checks workspace membership on every private route. Uploaded files use generated paths and are not authorized by a client-provided workspace ID alone.

## Why Does Open Innovation Matter?

Accounts-payable leakage is a practical problem for businesses that cannot afford a large finance or procurement team. An open implementation makes the workflow inspectable: owners can see how a product was matched, how an amount was calculated, and which source text supported the finding.

Open-weight models also make it possible to adapt normalization to supplier-specific language instead of treating every description as a generic chat prompt. A small business can run the deterministic fallback locally, inspect the training data, replace the model, or operate its own inference path without making the entire financial workflow dependent on a closed provider.

The most important design choice is not to ask the model to calculate money. Open innovation provides the language interpretation layer, while ordinary deterministic code remains responsible for the numbers and the audit trail.

## My Agent Session

No public agent-session transcript is attached to this submission.

## My First User
I tested an early version with a family-owned hardware tool shop. The workflow helped identify several invoice and purchase-order differences during testing. This was an informal product test, not a paying customer, so I am not claiming external revenue or a formal customer deployment.

## Prize Categories

- Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle

I am not claiming a measured Tinker performance prize result yet. The repository contains the real training and evaluation workflow, but model-comparison metrics should only be published after a Tinker training run and held-out inference run have produced the artifacts and measurements.
