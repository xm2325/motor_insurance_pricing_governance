# v0.21 — Shadow Deployment Bridge

v0.21 moves the pricing-governance case study from offline model validation into a deployable **shadow inference** pattern without changing the v0.20 model-family decision.

## Governance boundary

**Global model-family decision remains `HOLD`.**

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

## Model bundle

`build_deployment_bundle_v21.py` rebuilds the four v0.13/v0.20 model families using:

- 2022: training;
- 2023: aggregate calibration scale;
- 2024: reserved evaluation period.

The bundle contains four serialised pipelines, a manifest, categorical levels and parity fixtures. Every model artifact has a SHA-256 digest in the manifest. The service verifies those digests before loading the models.

The binary bundle is an Actions artifact rather than a committed repository binary.

## Deployment validation gates

The GitHub Actions workflow `.github/workflows/v21-deployment.yml` must pass all of the following:

1. leakage / temporal / evidence / deployment contract tests;
2. public data discovery, download and schema audit;
3. model-bundle rebuild;
4. 25-record direct-vs-API offline/online prediction parity;
5. deterministic repeated batch scoring;
6. rejection of current-outcome fields;
7. warning on an unseen categorical value;
8. 1,000-policy batch scoring;
9. Docker image build;
10. actual container startup with a read-only mounted model bundle;
11. HTTP `/health` and `/score` parity check against the direct model output.

Only after these gates pass should v0.21 be described as a deployable shadow-scoring demonstration.

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
