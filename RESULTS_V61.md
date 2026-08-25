# v0.61 — Prospective three-source request registration

## Decision context

v0.59 established that the historical request `MCR-XGB-MOTOR-001` is structurally blocked and cannot be repaired into promotion readiness by appending more evidence. v0.60 therefore created a prospective evidence-programme template requiring a separate future request, three pairwise-distinct fresh underlying source identities, a fixed target scope, ordered stages, and a sealed reserve.

v0.61 instantiates that template as **`MCR-XGB-MOTOR-002`**. It is a registration-only release. It does **not** execute S1, does not inspect any new source rows or outcomes, and does not change the historical 5/8 HOLD state.

## Scope frozen before fresh outcome access

The request scope is **`GLOBAL_TWO_TARGET`**. Frequency and pure-premium evidence are both required. A favourable result for one target cannot compensate for a failure of the other.

The registered target gate is carried forward unchanged:

- point relative deviance improvement >= 0.5%;
- paired-bootstrap q2.5 relative deviance improvement > 0;
- challenger absolute-log aggregate calibration error <= reference + 0.01;
- calibration scale must remain in the registered [0.5, 2.0] guard;
- all target conditions are conjunctive;
- any positive stage requires two independent GitHub Actions executions with matching decisions and registered point-metric reproducibility tolerance <= 0.1% relative.

No hyperparameter search or early stopping is allowed.

## Three source identities registered atomically

### S1 — temporal qualification: `pg15training`

Underlying source identity: **2015 Pricing Game French private motor TPL, 2009–2010**.

Pinned distribution metadata at CASdatasets commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`:

- `data/pg15training.rda`
- Git blob SHA-1 `9e670d214c05a7454d558ab32de5df96a6b0aba6`
- 1,934,161 bytes

Public provenance describes 100,000 policies and also documents 21 policy identifiers present in both 2009 and 2010, producing 100,021 policy-year rows. Those numbers are recorded as provenance expectations, **not** forced validation targets.

Before any outcome field may be read after stage opening, only `PolNum` and `CalYear` may be inspected. Every policy identifier appearing in more than one calendar year must be removed from all years. The observed duplicate count is descriptive and cannot be forced to equal 21.

After that pre-outcome leakage control:

- 2009 is the development year;
- deterministic SHA-256(`v61|S1|20260825|` + `PolNum`) gives an 80/20 train/calibration split with no outcome stratification;
- 2010 is the locked temporal test;
- no post-access resplit is permitted.

Frequency is `Numtppd + Numtpbi`; loss is `Indtppd + Indtpbi`; exposure is `Expdays / 365`.

### S2 — external replication: `swmotorcycle`

Underlying source identity: **Swedish motorcycle partial-casco portfolio, 1994–1998**.

Pinned metadata:

- `data/swmotorcycle.rda`
- Git blob SHA-1 `d48b2e78a94939f57d389110814037410a18c13c`
- 148,543 bytes

S2 is registered but **sealed** at v0.61 and may open only after reproducible S1 success. When permitted, its split is a fixed pinned-source-order random permutation, seed 20260828, 60/20/20 train/calibration/locked test, with no outcome stratification or resplit.

This portfolio is a model-family replication source only; it is not direct MTPL, UK or First Central transport evidence.

### S3 — sealed confirmation reserve: `brvehins1`

Underlying source identity: **Brazil SUSEP AUTOSEG vehicle-insurance portfolio, 2011**.

Its five RDA chunks are explicitly **one underlying source identity**, not five independent sources. All five pinned blob identities and a fixed a→e concatenation order are registered before access.

S3 remains sealed through S1 and S2. It may open only after reproducible success at both earlier stages and cannot rescue either failure. If opened, its fixed split is a 60/20/20 source-order permutation with seed 20260829.

This portfolio is model-family confirmation only; it is not direct MTPL, UK or First Central transport evidence.

## Source-contract lesson carried forward from v0.58

v0.58 demonstrated that authenticated source bytes can disagree with public documentation. v0.61 therefore separates three concepts:

1. **binary identity** — pinned repository commit, path, Git blob SHA-1 and byte size;
2. **semantic schema** — exact required column-name set and meanings;
3. **provenance expectations** — published counts and presentation order.

Column order and prose row counts are not identity gates. Required semantic fields remain fail-closed: if a registered stage opens and a required field is missing or renamed, the stage is consumed as a source-contract incident under v0.60; the protocol is not repaired after access.

## What v0.61 does not establish

v0.61 creates **no validation or model-performance evidence**. At registration:

- no new RDA has been downloaded or decoded;
- no new row-level source has been accessed;
- no new outcome value has been inspected;
- no model has been fitted;
- no performance metric or gate has been computed;
- S1, S2 and S3 are all unopened;
- S3 remains sealed;
- no promotion or customer pricing is authorised.

The historical project state remains **5/8 committee gates, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`**. v0.61 only creates a prospectively locked future request that can begin S1 after its registration is persisted on `main`.
