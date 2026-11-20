# PRIVASCOPE — Privacy-First Intelligent Observability & AIOps Platform

**Hackathon Build (CICADA 2026)** | Complete Local Prototype (Python + Streamlit + SQLite + Plotly + Scikit-learn)

## 1. Problem Statement
Modern enterprises rely on cloud observability and AIOps platforms to monitor servers, networks, and security events. However, shipping raw logs and telemetry directly to a central SaaS platform risks exposing passwords, API keys, authentication tokens, PII, and internal request payloads.

## 2. Proposed Solution: Two-Tier Privacy Architecture
**PRIVASCOPE** separates telemetry collection from cloud analytics using a strict two-tier boundary:

- **Tier 1 — Local Privacy Collector (On-Premise / Edge):**
  - Collects raw infrastructure, network, and security telemetry locally.
  - Detects and strips sensitive fields (`PASSWORD`, `API_KEY`, `auth_token`, `USERNAME`, `IP`, `raw_payload`) using a **strict allow-list** and regex redaction.
  - Buffers approved metadata in a local SQLite database during SaaS outages and replays without duplicates on recovery.
  - Writes an immutable local **Egress Proof & Privacy Audit** log proving exactly what left the environment.

- **Tier 2 — Central SaaS Observability & AIOps Platform:**
  - Receives only allow-listed, sanitized metadata.
  - Provides 12 interactive enterprise dashboards with dark SOC/AIOps styling.
  - Runs explainable ML anomaly detection (**Isolation Forest** with statistical Z-score fallback).
  - Correlates related alerts into root-cause incidents with confidence explanations and actionable recommendations.
  - Enforces strict **multi-tenant isolation** (`Tenant Alpha`, `Tenant Beta`, `Tenant Gamma`).
  - Demonstrates **Autonomous Operations** with human-in-the-loop approval, simulated execution, and rollback.

## 3. Technology Stack
- **Frontend:** Streamlit + Plotly (Dark Enterprise Theme)
- **Data & ML:** Pandas, NumPy, Scikit-learn (`IsolationForest`)
- **Persistence:** SQLite (`privascope.db`, auto-initialized on startup)
- **Testing:** `pytest` / `unittest`
- **Offline-Ready:** Runs 100% locally on Windows without Docker, Kubernetes, or paid APIs.

## 4. Quick Start (Windows)
### Option A: One-Click Startup
Double-click `run.bat` or run in PowerShell:
```powershell
.\run.bat
```

### Option B: Manual Setup
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 5. Running Automated Tests
```powershell
pytest -v
```
Tests verify:
1. **Privacy Allow-List:** Passwords, tokens, API keys, and unknown fields never enter outbound metadata.
2. **Collector Pipeline:** Raw telemetry normalizes, filters, and writes local audit records.
3. **Outage Buffer & Deduplication:** Events buffer in SQLite when SaaS is offline and flush with zero duplicates on recovery.
4. **Tenant Isolation:** Tenant Alpha, Beta, and Gamma data remain strictly isolated.
5. **AIOps Intelligence:** Normal baselines stay quiet while anomalous spikes generate explainable anomalies and correlated incidents.

## 6. Predefined Demo Scenarios
Use the sidebar **Demo Scenarios** selector to run any of the 8 built-in scenarios:
1. **Normal Operations** — Healthy baseline across all nodes.
2. **CPU Anomaly** — 95.4% CPU spike, ML anomaly, incident correlation, and remediation proposal.
3. **Security Attack** — 25 failed logins on `DB-01`; password redacted locally; sanitized metadata sent to SaaS.
4. **Network Failure** — High latency & packet loss with operational impact analysis.
5. **SaaS Outage & Local Buffer** — Disconnects SaaS, buffers metadata in SQLite, and replays on reconnect.
6. **Multiple Related Alerts** — Correlates CPU, latency, and HTTP 5xx alerts into one incident.
7. **Collector Offline** — Simulates heartbeat loss >60s, marks telemetry STALE, and proposes collector recovery.
8. **Privacy Demonstration** — Side-by-side Local vs Cloud Egress Proof showcase.

## 7. Limitations & Future Scope
- All remediation actions in Autonomous Operations are **simulated** for safety.
- Performance targets (p95 latency, alert latency) are measured in this local prototype and clearly labeled as such.
- Future scope includes OpenTelemetry (OTLP) receivers, mTLS collector-to-SaaS transport, and cryptographic hash-chaining of egress audit logs.
