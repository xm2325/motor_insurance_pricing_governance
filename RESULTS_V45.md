# v0.45 — Repository front-door and interview-evidence sync

## Purpose

Bring the repository entry points up to the same evidence state as the project itself. Before v0.45, the README and Interview Evidence Pack still centred on v0.35-era Spanish validation even though v0.36–v0.44 had added two preregistered external portfolios, numerical-reproducibility controls, validation-consumption ledgers, an aggregate model-risk synthesis and a fail-closed Model Change Committee readiness gate.

v0.45 changes **documentation and evidence navigation only**. It does not access row-level data, fit/recalibrate a model, change historical gates, or create new validation evidence.

## README front door

The first section of `README.md` is regenerated idempotently while every historical detailed evidence section after the first `---` separator is preserved byte-for-byte.

The new 30-second story surfaces:

- the 5.43% freMTPL2 development signal and its non-commercial boundary;
- Spanish 2024 first-use OOT and current `CONSUMED_RETROSPECTIVE_VALIDATION` status;
- Australian preregistered mixed/negative external evidence;
- the numerical-reproducibility lesson from Australia;
- Belgian preregistered negative gates and two-run numerical reproduction;
- **0/4 preregistered Australian/Belgian external target gates passing**;
- v0.43 `HOLD / HOLD_SHADOW_ONLY`, `promotion_review_status=NOT_OPEN`;
- v0.44 `EVIDENCE_GAP_HOLD`, **5/8** machine gates passing with three evidence blockers;
- the distinction between operational controls and model approval.

## Interview Evidence Pack

`INTERVIEW_EVIDENCE_PACK.md` is rewritten around the complete evidence chain rather than stopping after Spanish OOT/rolling-origin work. It includes a 20-second version, a structured walkthrough, likely questions, an updated STAR story and explicit claims to avoid.

The pack does not say that XGBoost is universally worse, that the 0.5% Belgian materiality threshold is an industry standard, that a committee approved the model, or that any result transports to FIRST CENTRAL/current UK motor pricing.

## Protection

CI checks that:

- the README refresh is idempotent;
- the historical README body is preserved;
- v0.36–v0.44 results and current review/committee packs are reachable from the front door;
- Spanish 2024 is described as first-use locked OOT but currently consumed validation;
- the Interview Evidence Pack contains the external-validation, numerical-reproducibility and committee-gate evidence;
- scientific/approval/UK-transfer boundaries remain explicit;
- every latest-results link referenced by the front door exists.

The machine summary records SHA-256 digests for README, Interview Evidence Pack and Evidence Registry after synchronisation.
