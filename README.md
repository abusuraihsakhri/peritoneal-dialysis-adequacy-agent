# Peritoneal Dialysis Adequacy Agent

> **Domain:** Nephrology & Renal Replacement Protocols
> **Reference Guidelines & Standards:** `KDIGO & KDOQI Clinical Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Peritoneal Dialysis Adequacy Agent** is an advanced analytical and computational platform implementing 4-Hour Peritoneal Equilibration Test (PET) Transport Classifier. It evaluates peritoneal dialysis adequacy through multi-agent consensus, providing clinical decision support for nephrology teams.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`DPCreatinineRationAgent`**: Specialized Sub-Agent 1 for peritoneal-dialysis-adequacy-agent
- **`WeeklyKtVPeritonealAgent`**: Specialized Sub-Agent 2 for peritoneal-dialysis-adequacy-agent
- **`UltrafiltrationFailureAgent`**: Specialized Sub-Agent 3 for peritoneal-dialysis-adequacy-agent

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Setup
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/peritoneal-dialysis-adequacy-agent.git
cd peritoneal-dialysis-adequacy-agent

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Optional: Set a persistent audit secret key for HMAC-SHA256 audit trail
# If not set, a random key will be generated for the session
AUDIT_SECRET_KEY=your-secure-secret-key-here
```

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Audit Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Query the Supervisory Chat
```bash
python cli.py chat "What is the current system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--task-id` | Unique task/case identifier | `TASK-2026-001` |
| `--target` | Target identifier (patient key, specimen) | `KEY-TARGET-01` |
| `--primary` | Primary metric value (float) | `28.5` |
| `--secondary` | Secondary metric value (float) | `14.2` |
| `--critical` | Flag for critical/emergency cases | `False` |
| `--status` | Status descriptor (NOMINAL, DISCORDANT, etc.) | `DISCORDANT` |

### Input Data Schema (CSV Batch)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional |
| `status_descriptor` | Status code or phenotype | Optional |
| `is_critical_flag` | Emergency escalation flag | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

### Run the automated test suite:
```bash
pytest -v
```

### Run with coverage:
```bash
pytest -v --cov=agents --cov-report=term-missing
```

### Execute high-throughput batch simulation benchmarks:
```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Build and run with Docker:
```bash
docker build -t peritoneal-dialysis-adequacy-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key peritoneal-dialysis-adequacy-agent
```

### Using Docker Compose:
```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
peritoneal-dialysis-adequacy-agent/
├── agents/                          # Core agent modules
│   ├── __init__.py                  # Package initialization
│   ├── api.py                       # FastAPI REST endpoints
│   ├── base.py                      # Security, PHI guard, audit trail
│   ├── learning.py                  # Bayesian calibration engine
│   ├── llm_factory.py               # LLM provider factory
│   ├── metrics.py                   # Prometheus metrics collector
│   ├── models.py                    # Pydantic data models
│   ├── streamer.py                  # WebSocket telemetry streamer
│   ├── supervisor.py                # Master orchestrator
│   └── workers.py                   # Specialized worker agents
├── tests/                           # Test suite
│   ├── test_enrichment.py           # Enrichment module tests
│   └── test_peritoneal_dialysis_adequacy_agent.py  # Core agent tests
├── cli.py                           # Command-line interface
├── pd_sentinel.py                   # PD-Sentinel standalone module
├── enrichment.py                    # Feature enrichment engines
├── simulator.py                     # High-throughput simulation
├── sample.csv                       # Sample input data
├── sample_payload.json              # Sample API payload
├── benchmark_dataset.json           # Benchmark test cases
├── pyproject.toml                   # Project configuration
├── Dockerfile                       # Container build
├── docker-compose.yml               # Container orchestration
└── README.md                        # This file
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
