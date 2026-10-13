# Peritoneal Dialysis Adequacy Agent

Educational tools for calculating **4-hour PET dialysate-to-plasma creatinine (D/P)** and **weekly urea Kt/V** in adult chronic peritoneal dialysis. A standalone browser interface, Python functions, CLI and FastAPI endpoints use the same explicitly documented formulas.

**Clinical limitation:** These results do not establish adequacy of dialysis, select an exchange prescription, or replace clinical assessment. The four PET groups use *historical illustrative thresholds*, not universally valid ISPD cutoffs. Do not enter patient-identifiable data.

## Live application

The static interface is maintained in [web/index.html](web/index.html). A GitHub Pages deployment workflow is provided; a public deployment link will be listed here only after the site is confirmed reachable.

## Features

- **PET:** 4-hour D/P creatinine = dialysate creatinine / plasma creatinine, with historical low, low-average, high-average and high descriptive bands.
- **Weekly Kt/V:** peritoneal component from pooled 24-hour dialysate urea and drain volume; optional residual renal component from 24-hour urine urea and volume. Total is the sum.
- **Validation:** finite nonnegative measurements, nonzero plasma/serum denominator and urea distribution volume, paired optional urine inputs, and protection against nonfinite results.
- **Interfaces:** static browser calculator with local JSON export; Python package functions; CLI commands; FastAPI `/api/pet` and `/api/ktv`.
- **Legacy compatibility:** existing generic agent audit, supervisory chat, batch commands and API routes remain available. Their arbitrary primary/secondary metric alerts are **demonstrations, not clinical PD algorithms**.

## Browser usage

Open the deployed Pages site when available. For local use, serve the directory so ES modules load correctly:

```bash
python -m http.server 8080 --directory web
# Open http://127.0.0.1:8080
```

Enter matching creatinine concentration units for PET. For Kt/V, use matched serum/dialysate/urine urea units, 24-hour effluent and urine volumes in litres, and an independently calculated urea distribution volume V in litres. Leave **both** urine inputs blank to omit the renal component. Results are educational only. Downloaded JSON contains the calculated outputs and interpretation.

**Data handling:** The browser calculation runs entirely in JavaScript without a backend, account, telemetry or persistent storage; no clinical input is uploaded by the application. The server/API legacy components have separate runtime and security considerations. Regex-based identifier detection is not sufficient to certify HIPAA compliance. Use synthetic data.

## Python installation

Python 3.10 or newer:

```bash
python -m pip install -e ".[api,dev]"
python -m pytest -q
node --test tests/web.test.mjs
```

A regular installation requires only Pydantic; use `.[api]` to install FastAPI and Uvicorn, and `.[dev]` for test/build tooling. Node.js 22 or newer is used for browser-module regression tests, not for the deployed app.

```bash
# 4-hour PET D/P creatinine, illustrative transport band
peritoneal-dialysis-adequacy-agent pet --dialysate-creatinine 6.8 --plasma-creatinine 10

# 24-hour collection-based weekly urea Kt/V (including residual renal)
peritoneal-dialysis-adequacy-agent ktv --serum-urea 50 --dialysate-urea 40 \
  --daily-drain-volume-l 10 --v-l 40 --urine-urea 150 --daily-urine-volume-l 0.5

# Legacy generic agent commands (not a clinical PET/Kt/V interpretation)
python cli.py audit --task-id DEMO-1 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
```

The historic `peritoneal-dialysis-adequacy-engine` console command remains as an alias. The source functions are `pet_creatinine` and `weekly_ktv` in `peritoneal_dialysis_adequacy_agent/clinical.py`.

## API and container

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# Visit http://127.0.0.1:8000/docs
```

```bash
curl -X POST http://127.0.0.1:8000/api/pet \
  -H "Content-Type: application/json" \
  -d '{"dialysate_creatinine_4h":6.8,"plasma_creatinine":10}'

curl -X POST http://127.0.0.1:8000/api/ktv \
  -H "Content-Type: application/json" \
  -d '{"serum_urea":50,"dialysate_urea":40,"daily_drain_volume_l":10,"urea_distribution_volume_l":40}'
```

For Docker Compose, set a unique runtime `AUDIT_SECRET_KEY` in your environment before launching:

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose up --build
```

The legacy audit trail is an **in-memory HMAC hash chain**; it is not persisted across restarts. Its verification recomputes entry signatures but cannot reconstruct discarded original event payloads. Never reuse the key previously included in repository history, and do not expose the API publicly without authentication and access controls.

## Method, evidence and limitations

- **PET:** A standardized PET protocol is needed; 4-hour D/P creatinine measurements depend on sampling and assay correction. Historical example cutoffs of 0.50, 0.65, and 0.81 are descriptive rather than universal diagnostic thresholds. The ISPD 2021 membrane guidance favors interpretation of peritoneal solute transfer rate and appropriate local context: [Morelle et al., 2021](https://doi.org/10.1177/0896860820982218).
- **Kt/V:** Weekly peritoneal = `7 × (D_urea / P_urea) × daily_effluent_L / V_L`; residual renal = `7 × (U_urea / P_urea) × daily_urine_L / V_L`. These approximate clearances must be interpreted with symptom burden, volume status, biochemical measures, residual kidney function and individual goals: [Brown et al., ISPD 2020](https://doi.org/10.1177/0896860819895364).
- **Caveat:** Current clinical recommendations do not establish a single Kt/V number as proof of adequate dialysis. A healthcare professional must review any clinical use; this repository is not validated as a medical device.

## Quality checks and deployment

The CI workflow runs Python 3.10–3.12 tests, Python package build, Node browser formula tests and dependency auditing. A separate workflow deploys the static `web/` directory to GitHub Pages from `master` when repository Pages is enabled. The browser needs no Pyodide or backend because these equations are implemented natively in JavaScript.

## Technology and license

Python 3.10+, Pydantic 2, optional FastAPI/Uvicorn, vanilla JavaScript ES modules, HTML/CSS, pytest and Node.js tests. Modern evergreen desktop and mobile browsers with ES module support are required; no older-browser support is claimed.

Released under the [MIT License](LICENSE).
