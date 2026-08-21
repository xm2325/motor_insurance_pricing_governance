# v0.21 — Shadow Deployment Bridge

v0.21 moves the pricing-governance case study from offline model validation into a deployable **shadow inference** pattern without changing the v0.20 model-family decision.

## Verified status

GitHub Actions run **32481705152** completed successfully.

Verified gates:

- deployment/governance contracts: **pass**;
- public source discovery/download/schema audit: **pass**;
- four-model locked bundle rebuild: **pass**;
- 25-record direct-vs-API parity: **max absolute error 0.0**;
- forbidden current-outcome field rejection: **pass**;
- unseen-category warning: **pass**;
- repeated batch determinism: **pass**;
- 1,000-policy batch: **pass**;
- Docker image build: **pass**;
- container startup with read-only mounted model bundle: **pass**;
- network HTTP `/score` parity: **pass**.

The CI TestClient 1,000-policy batch diagnostic had median **43.0 ms** and p95 **74.1 ms** across five runs. This is an environment-specific smoke benchmark, not a production SLA.

The complete binary model bundle is stored as the Actions artifact `motor-pricing-shadow-deployment-v21`; only audit evidence and the manifest are committed.

## Governance boundary

**Global model-family decision remains `HOLD`.** The serving manifest exposes this as `HOLD_SHADOW_ONLY`.

The service therefore does not expose a quote or price endpoint. It returns reference and challenger **risk-model outputs side by side** so they can be compared in shadow mode.

It is not a production pricing engine and is not evidence of transfer to FIRST CENTRAL or the UK motor market.

## API

FastAPI routes:

- `GET /health` — service/model-contract status;
- `GET /model-info` — model version, temporal roles, artifact metadata and governance boundary;
- `POST /score` — one leakage-controlled policy feature record;
- `POST /batch-score` — 1–1,000 policy records.

No `/quote` or `/price` route exists.

Each score includes:

- Poisson GLM reference frequency;
- XGBoost Poisson challenger frequency;
- Tweedie GLM reference pure-premium risk score;
- XGBoost Tweedie challenger pure-premium risk score;
- challenger/reference log-risk disagreement;
- warnings for categorical values not seen in the 2022 training data.

## Feature contract

The online contract matches the locked OOT feature set exactly: 14 driver, vehicle and policy characteristics.

The request schema rejects extra fields. Current outcomes, premium, exposure, year, customer ID and policy status are therefore rejected rather than silently ignored.

Training and online inference use a common canonical representation for categorical values.

## Model bundle and integrity

`build_deployment_bundle_v21.py` rebuilds the four v0.13/v0.20 model families using:

- 2022: training;
- 2023: aggregate calibration scale;
- 2024: reserved evaluation period.

The verified compressed joblib artifacts from run 32481705152 are approximately:

- Poisson GLM frequency: **3.4 KB**;
- XGBoost Poisson frequency: **190.7 KB**;
- Tweedie GLM pure premium: **3.5 KB**;
- XGBoost Tweedie pure premium: **208.9 KB**.

Every artifact has a SHA-256 digest in `action_results/v21/manifest.json`. The service verifies those digests before loading the models. The feature contract is itself SHA-256 versioned.

## Deployment validation gates

`.github/workflows/v21-deployment.yml` enforces:

1. leakage / temporal / evidence / deployment contract tests;
2. public data discovery, download and schema audit;
3. model-bundle rebuild;
4. direct-vs-API offline/online prediction parity;
5. deterministic repeated batch scoring;
6. rejection of current-outcome fields;
7. warning on unseen categorical values;
8. maximum 1,000-policy batch scoring;
9. Docker image build;
10. actual container startup with a read-only mounted model bundle;
11. HTTP `/health` and `/score` parity against direct model output.

## Run locally

With the 2022–2024 public source already downloaded:

```bash
python build_deployment_bundle_v21.py
python smoke_test_deployment_v21.py
uvicorn deployment.app:app --host 0.0.0.0 --port 8000
```

Container:

```bash
docker build -t motor-pricing-shadow:v21 .
docker run --rm -p 8000:8000 \
  -e MODEL_BUNDLE_DIR=/models \
  -v "$PWD/deployment_artifacts:/models:ro" \
  motor-pricing-shadow:v21
```

## Why this matters for model governance

The project deliberately separates **model promotion** from **model deployability**. A challenger can be technically deployable and observable in shadow mode while still failing the evidence threshold for a pricing-model family change. v0.21 demonstrates that separation explicitly.
