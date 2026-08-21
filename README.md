# Motor Insurance Pricing & Model Governance Workbench

A reproducible motor-insurance pricing project covering GLM and gradient-boosting benchmarks, expected-loss modelling, locked validation, monitoring, model-change governance and out-of-time (OOT) validation.

## Validation tracks

### freMTPL2 governance benchmark

The existing project work uses the public French `freMTPL2` portfolio to test:

- Poisson GLM vs XGBoost claim-frequency modelling;
- Gamma severity and Tweedie / two-part expected-loss modelling;
- train / calibration / final-test separation;
- calibration, lift, segment stability and paired bootstrap uncertainty;
- shadow monitoring, PSI, unseen-category and severity-inflation stress tests;
- model-change disagreement, exact log-risk attribution and investigation of high-disagreement cohorts.

The key governance conclusion through v0.10 is deliberately conservative: stronger claim-frequency ranking did not provide enough stable expected-loss evidence to promote the challenger, so the decision remained **HOLD pending new out-of-time evidence**.

### v0.11 — real calendar OOT validation

v0.11 adds a second public Spanish motor portfolio with explicit renewal dates. It is intentionally separate from the freMTPL2 random-split benchmark.

The GitHub Actions workflow `.github/workflows/spanish-oot.yml`:

1. downloads the public CSV over the runner network;
2. records SHA-256, byte size, row/column count, schema and renewal-date range;
3. requires at least two calendar years with sufficient rows;
4. trains only on earlier renewal years;
5. evaluates on the latest sufficiently populated renewal year;
6. uploads all audit and OOT outputs as a workflow artifact.

The workflow **fails rather than calling a random split OOT** if the source does not support a valid calendar split. A successful workflow is required before any CV/report claims a real OOT result.

## Run the OOT track

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_spanish_motor.py
python run_spanish_oot.py
```

Key outputs:

- `results_oot/spanish_data_audit.json`
- `results_oot/oot_frequency_model_comparison.csv`
- `results_oot/oot_pure_premium_model_comparison.csv`
- `results_oot/oot_summary.json`

## Scope

This is a portfolio model-governance project, not a production pricing engine. Pure-premium estimates do not include company-specific expenses, reinsurance, commercial adjustments or regulatory approval. Synthetic proposition simulations are kept separate from real insurance outcomes.
