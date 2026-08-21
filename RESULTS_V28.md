# v0.28 — Shadow Release Registry & Operator-Authorised Rollback

## Decision

**PASS — release-control and rollback mechanics verified; model-family governance remains `HOLD / HOLD_SHADOW_ONLY`.**

v0.28 does not retrain a model during rollback, change a customer price, or automate a serving switch from a monitoring/review signal. It adds an auditable release-control layer around integrity-verified v0.27 shadow bundles.

## Verified behaviour

A single fitted hybrid model set is sealed twice with different release provenance:

- `shadow-release-a`: designated last-known-good after explicit activation plus GREEN monitoring evidence;
- `shadow-release-b`: later shadow release under synthetic review-control testing.

The two packages have **different content-addressed lock digests but identical hashes for all 9 locked model/content artifacts**. This isolates release-control behaviour from retraining variation.

The deterministic registry replay verifies:

1. A and B are registered only after v0.27 content-addressed integrity verification.
2. A is explicitly activated and then marked last-known-good with GREEN monitoring evidence.
3. B is explicitly activated.
4. A synthetic HIGH review is opened against B; **B remains active** — the review itself causes no serving change.
5. An unauthorised rollback attempt is rejected with `Rollback activation requires explicit operator authorisation`; B remains active.
6. The registry selects A as the only valid rollback target because A is the prior integrity-verified last-known-good release.
7. An explicitly operator-authorised rollback switches active shadow release from B back to A.
8. No model retraining and no pricing change occurs during rollback.
9. The release event chain verifies across **7 hash-linked events**.

## Container switch evidence

GitHub Actions builds the CPU-only shadow runtime image **once** and mounts the two release bundles sequentially:

| Check | Candidate B | Rollback A |
|---|---:|---:|
| Mounted lock identity | distinct release-B digest | distinct release-A digest |
| Same-fit records | 25 | 25 |
| Core fields / record | 4 | 4 |
| HTTP comparisons | **100** | **100** |
| Max absolute error | **0.0** | **0.0** |
| Governance | `HOLD_SHADOW_ONLY` | `HOLD_SHADOW_ONLY` |

The service therefore demonstrates a real bundle-identity switch using the same container image while preserving the validated scoring outputs.

## Release registry controls

`deployment/release_registry.py` enforces:

- only `HOLD_SHADOW_ONLY` bundles can be registered;
- only `CONTENT_ADDRESSED_BUNDLE_VERIFIED` contract-0.27 bundles can enter the registry;
- release IDs are unique;
- activation requires explicit `operator_authorised=True`;
- last-known-good status requires an active release, GREEN monitoring evidence and explicit operator authorisation;
- review opening is evidence-only and never changes serving;
- rollback target selection is restricted to the prior last-known-good release;
- rollback activation requires explicit operator authorisation;
- every registry transition is chained using SHA-256 event hashes;
- sealed `release_label` must match the registry release ID in the replay, preventing package-identity mix-ups.

## Interpretation boundary

The HIGH review signal in this version is deliberately **synthetic** and tests release-control behaviour. It is not an observed production incident.

`operator_authorised=True` is a governance contract in this portfolio implementation, not an identity/authentication/approval system. A production implementation would require real IAM, separation of duties, protected deployment environments, immutable artifact storage and organisation-specific approval policy.

The rollback changes only which already-verified shadow bundle is mounted. It does not approve XGBoost for customer pricing and does not establish transfer to FIRST CENTRAL or the UK motor market.
