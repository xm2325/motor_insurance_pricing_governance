# v0.23 — Monitoring-to-Review Lifecycle

v0.23 turns v0.22 aggregate monitoring alerts into a deterministic review lifecycle. It does **not** change the global model-family decision (`HOLD / NO PROMOTION`) or the serving boundary (`HOLD_SHADOW_ONLY`).

## Why this layer exists

A monitoring threshold breach should not automatically become a model or pricing change. A single noisy window should also not create repeated open/close alerts.

The v0.23 demonstration policy therefore uses simple hysteresis:

- **2 consecutive breach windows** are required to open a review;
- **2 consecutive green windows** are required to close an open review;
- the controller issues **review recommendations only**;
- it never changes customer pricing, model approval, rollback state, or serving configuration automatically.

These are project demonstration rules, not insurer or regulatory thresholds.

## Evidence lineage

The lifecycle consumes only the persisted aggregate v0.22 monitoring evidence in `action_results/v22/monitoring_replay_summary.json`.

No raw policy payload, customer ID, or row-level feature record is copied into the review evidence. Each review window is reduced to aggregate metrics and receives a SHA-256 evidence digest.

The replay is deterministic for identical monitoring evidence.

## Real 2024 temporal-drift review

The real 2024 monitoring replay has one active alert: `feature_drift`.

Key evidence:

- max feature PSI: **1.4116**;
- maximum-drift feature: **`business_type`**;
- frequency challenger/reference disagreement p95: **0.2715**;
- pure-premium challenger/reference disagreement p95: **0.8257**.

The lifecycle is:

```text
2022 control                 HEALTHY
2024 temporal window 1      WATCH
2024 temporal window 2      REVIEW_REQUIRED
```

The opened review is classified **MEDIUM** with the recommendation:

> `REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION`

This is deliberately different from a model-disagreement incident. v0.22 showed that 2024 portfolio mix changed materially while challenger/reference disagreement stayed broadly stable.

## Recovery hysteresis

After the temporal review is open:

```text
first green recovery window   RECOVERING
second green recovery window  HEALTHY
```

The first review is closed only after two consecutive green windows.

This demonstrates alert/review hysteresis rather than automatic model rollback.

## Synthetic high-severity review

The final two windows reuse the explicitly synthetic v0.22 stress evidence. They contain:

- schema/error-rate breach;
- unseen-category breach;
- feature drift;
- pure-premium model-disagreement breach.

The lifecycle becomes:

```text
synthetic stress 1    WATCH
synthetic stress 2    REVIEW_REQUIRED
```

The second review is classified **HIGH** with the recommendation:

> `INVESTIGATE_SERVING_DATA_AND_MODEL`

This is a monitoring-controller validation scenario, not an observed production incident.

## Verified state sequence

The GitHub Actions replay verifies the exact sequence:

```text
HEALTHY
WATCH
REVIEW_REQUIRED
RECOVERING
HEALTHY
WATCH
REVIEW_REQUIRED
```

It also verifies that:

- the real temporal review is driven only by `feature_drift`;
- recovery closes the review after two green windows;
- the synthetic stress review is independent of the earlier review;
- evidence remains aggregate-only;
- identical input evidence produces an identical lifecycle;
- `automatic_model_or_pricing_change` remains `false`.

## Governance interpretation

The project now separates five layers:

1. **predictive evidence** — does the challenger improve the target?;
2. **model-change approval** — is the gain stable enough to promote?;
3. **shadow deployability** — can reference/challenger scores be served safely?;
4. **monitoring** — has serving, population mix or model disagreement changed?;
5. **review lifecycle** — is a breach persistent enough to require investigation, and has it recovered long enough to close?

The global decision is unchanged:

> **HOLD / NO MODEL-FAMILY PROMOTION; serving remains HOLD_SHADOW_ONLY.**
