# v0.25 — CPU-only runtime slimming

## Question

Can the shadow-serving image be separated from the training/development environment without changing scores or weakening the existing governance boundary?

v0.25 treats this as a deployment-engineering change, not a modelling change. The locked v0.21 model bundle, feature contract, monitoring logic and `HOLD_SHADOW_ONLY` status are unchanged.

## Change

The historical container installed the full project `requirements.txt`, including training, plotting, testing and benchmark dependencies. The production `Dockerfile` now installs `requirements-runtime.txt` instead.

The runtime dependency set is limited to NumPy, pandas, SciPy, scikit-learn, `xgboost-cpu`, joblib, FastAPI and uvicorn. XGBoost documents `xgboost-cpu` as the minimal CPU-only distribution with a substantially smaller disk footprint than the full package.

## Acceptance design

The v0.25 GitHub Actions benchmark builds two images from the same commit and mounts the same locked model bundle into both:

1. **full baseline image** — historical `requirements.txt`;
2. **CPU-only runtime image** — `requirements-runtime.txt`.

The change is accepted only if all of the following pass:

- runtime image is at least 20% smaller than the full baseline;
- runtime image contains `xgboost-cpu` and excludes `matplotlib`, `pytest`, `tabulate`, `httpx` and `nvidia-nccl-cu13`;
- both containers report the same health payload and `HOLD_SHADOW_ONLY` governance status;
- 25 locked parity records match across six HTTP score fields between full and CPU-only images;
- the four core runtime predictions also match the persisted offline parity reference.

## Verified result

Successful workflow evidence is persisted under `action_results/v25/`.

| Check | Verified result |
|---|---:|
| Full baseline image | **960,271,925 bytes** |
| CPU-only runtime image | **488,778,419 bytes** |
| Bytes removed | **471,493,506 bytes** |
| Relative image reduction | **49.10%** |
| Minimum acceptance gate | 20% |
| Runtime XGBoost distribution | `xgboost-cpu 3.4.0` |
| Forbidden runtime packages present | **0** |
| Locked parity records | **25** |
| Full vs runtime numeric fields / record | **6** |
| Full vs runtime max absolute error | **0.0** |
| Runtime vs offline reference fields / record | **4** |
| Runtime vs offline max absolute error | **0.0** |
| Governance status | **HOLD_SHADOW_ONLY** |

The measured image reduction is therefore approximately half of the historical image while preserving exact scores on the locked parity set.

## What the result does and does not establish

The result supports a narrower serving dependency boundary and verifies exact parity for the tested locked bundle and records. It does **not** change model-family approval, calibration evidence, pricing logic, monitoring thresholds or the `HOLD` decision.

It also does not establish unrestricted cross-version model portability. The benchmark training environment resolved `xgboost 3.4.1`, while the CPU-only runtime used `xgboost-cpu 3.4.0`. HTTP parity was exactly 0.0-error on the locked test set, but XGBoost emitted a warning when the joblib/pickle-serialised model was loaded across versions.

XGBoost's own model-I/O guidance distinguishes stable model files from pickle-style memory snapshots: native model files are intended for long-term compatibility, while pickle/joblib snapshots are not guaranteed to be portable across XGBoost versions. That warning is therefore retained as an explicit v0.25 limitation rather than suppressed.

## Next engineering gate

The next deployment upgrade should address model-environment portability directly:

- persist training-library versions in the model manifest;
- expose or record runtime-library versions;
- add an explicit compatibility decision at bundle load;
- migrate XGBoost components toward native `save_model` / JSON or UBJSON artefacts where practical, rather than relying only on joblib/pickle snapshots;
- rerun offline/HTTP parity after any serialization-format change.

Until that work is complete, v0.25 should be interpreted as **runtime slimming with verified current parity**, not a claim of arbitrary-version portability.
