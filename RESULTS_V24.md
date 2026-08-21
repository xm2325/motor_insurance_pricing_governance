# v0.24 — CI Stratification and Verified Source Cache

v0.24 changes the project delivery pipeline rather than the insurance models. The model-family decision remains **HOLD / NO PROMOTION** and serving remains **HOLD_SHADOW_ONLY**.

## Problem

Before v0.24, both v0.21 deployment and v0.22 monitoring workflows used a broad `deployment/**` path trigger. A review-layer-only change such as `deployment/review.py` therefore caused the heavy pipelines to:

- install the full modelling stack;
- download the 94.7 MB Spanish motor source again;
- audit the source;
- rebuild four locked models;
- rerun parity/replay checks;
- build Docker images and run network smoke tests.

Persisted evidence assertions were also repeated inside heavy jobs even though a PR-time heavy rerun could not update the already committed evidence being asserted.

## Change 1 — explicit CI ownership

The heavy v0.21/v0.22 workflows now list their actual serving/monitoring dependencies explicitly instead of `deployment/**`.

`deployment/review.py` belongs to the lightweight v0.23 review workflow and is intentionally **not** a dependency of v0.21 or v0.22.

Persisted Evidence Registry checks remain in the lightweight CI.

Static contracts in `tests/test_ci_stratification_v24.py` fail if the broad `deployment/**` trigger is reintroduced, if review code becomes a heavy dependency, or if cache/concurrency controls disappear.

## Real trigger-routing proof

After merging the CI-stratification foundation, PR #7 was created with a one-file diff affecting only `deployment/review.py`.

GitHub created exactly one relevant workflow run for head SHA `67bd1e846bbf05161320f1e6ae14dec81c2514ae`:

- `Motor pricing review lifecycle v0.23` — run `32502291078`.

No v0.21 deployment run and no v0.22 monitoring run were created for that review-only diff.

This is the end-to-end proof that review-layer iteration no longer causes model retraining / Docker rebuild work.

## Change 2 — verified public-data cache

The version-1 public Mendeley source is cached under:

`spanish-motor-sw4jmdb2sm-v1-${runner.os}`

Cache reuse is fail-closed. `download_spanish_motor_2022_2024.py` accepts a cached file only when all of the following remain true:

1. the dataset version is still the expected version;
2. Mendeley metadata reports the verified size;
3. local cached size matches;
4. local SHA-256 matches the registered source digest.

Verified source files:

| File | Bytes | SHA-256 |
|---|---:|---|
| `Dataset of motor insurance portfolio.csv` | 94,710,312 | `6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4` |
| `Descriptive of variables.xlsx` | 15,413 | `cde44e797a7fd34de29199c78c9301d6f00ed94fd725b4fe8e67e6c2c4cc2e41` |

The first migration validation had a cache miss, performed the normal network download, revalidated the source and saved the cache.

A second controlled v0.21 run (`32501948128`) then logged:

- `Cache hit for: spanish-motor-sw4jmdb2sm-v1-Linux`;
- main CSV: `source_mode = VERIFIED_CACHE_HIT`, `cache_hit = true`;
- variable workbook: `source_mode = VERIFIED_CACHE_HIT`, `cache_hit = true`.

The full source schema audit, model-bundle rebuild, offline/online parity and Docker/network parity all still passed after the cache hit. Cache therefore removes repeated source transfer without removing integrity or modelling checks.

## Change 3 — superseded-run cancellation

v0.21, v0.22 and lightweight CI now use workflow concurrency with `cancel-in-progress: true` per branch/ref. New commits can cancel superseded work instead of leaving multiple expensive heavy runs active for the same PR.

## Automated contracts

`tests/test_download_cache_v24.py` checks that:

- size + SHA-256 are both required for cache acceptance;
- modified cached bytes are rejected;
- changed source metadata fails closed.

`tests/test_ci_stratification_v24.py` checks that:

- `deployment/**` is absent from v0.21/v0.22 triggers;
- `deployment/review.py` is absent from heavy dependencies;
- explicit serving/monitoring dependencies remain present;
- source caching and concurrency cancellation remain configured;
- Evidence Registry validation remains owned by lightweight CI.

The migration validation passed lightweight CI, v0.21 deployment and v0.22 monitoring end to end.

## Remaining delivery bottleneck

The source download is no longer the dominant repeated cost. The next obvious inefficiency is dependency/container weight: the current full requirements install includes training/reporting packages and the Linux XGBoost distribution pulls a roughly **252 MB NCCL dependency** in the observed GitHub runner/container build.

That is a separate v0.25 problem. v0.24 does not claim container slimming yet.
