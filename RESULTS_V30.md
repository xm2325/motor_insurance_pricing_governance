# v0.30 — Attestation-aware Shadow Release Admission

## Decision

**PASS — a sealed release archive is admitted only after GitHub/Sigstore provenance, exact subject identity, archive-safety checks and the inner v0.27 content-addressed bundle all verify. The decision is `ADMIT_TO_SHADOW_REGISTRY_ONLY`; model-family governance remains `HOLD / HOLD_SHADOW_ONLY`.**

v0.30 turns the v0.29 build attestation into a release-admission gate. It does not promote the challenger, calculate customer prices or claim production safety.

## Verified PR-run evidence

GitHub Actions run `32602099555` built a fresh bundle from the audited public Mendeley source, sealed it with the v0.27 lock, packaged it deterministically, generated a GitHub/Sigstore build-provenance attestation and applied the v0.30 admission policy.

| Check | Result |
|---|---:|
| Archive | `motor-pricing-shadow-bundle-v30.tar.gz` |
| Archive bytes | **386,588** |
| Archive SHA-256 | `80bac00691af49f23e3220cba1d7d90ffd255c118dbf2f67d3688e8d3f95a177` |
| GitHub attestation ID | **42362866** |
| Exact repository identity | `xm2325/motor_insurance_pricing_governance` |
| Exact workflow | `Motor pricing attested release admission v0.30` |
| Workflow path | `.github/workflows/v30-admission.yml` |
| Verified timestamp records | **1** |
| Predicate | SLSA provenance v1 |
| Build type | GitHub Actions workflow v1 |
| Archive members | **12** |
| Raw source-data members | **0** |
| Inner bundle integrity | `CONTENT_ADDRESSED_BUNDLE_VERIFIED` |
| Inner lock artifacts | **9** |
| Inner locked bytes | **1,604,579** |
| Source dataset | Mendeley `sw4jmdb2sm` v1 |
| Governance | `HOLD_SHADOW_ONLY` |
| Admission decision | `ADMIT_TO_SHADOW_REGISTRY_ONLY` |

Attestation page for this verified PR run:

`https://github.com/xm2325/motor_insurance_pricing_governance/attestations/42362866`

The exact archive and lock digests are build identities and will legitimately change when the workflow/ref/build provenance changes. Persisted branch evidence is therefore the canonical source after the final push run.

## Four admission layers

1. **Platform provenance** — `gh attestation verify` must cryptographically verify the exact archive against this repository.
2. **Attestation policy** — the verified statement must bind the exact archive name/SHA-256 to the expected repository and v0.30 workflow identity.
3. **Packaging safety** — no absolute/traversal paths, symlinks/hardlinks or raw public source dataset are allowed in the archive; required sealed-bundle files must be present.
4. **Inner model bundle** — the extracted bundle must pass the v0.27 content-addressed lock, preserve the audited source provenance and remain `HOLD_SHADOW_ONLY`.

Passing all four layers authorises only entry to the shadow release registry.

## Negative admission tests

Three deliberately invalid candidates were rejected:

- a byte was appended to the release archive: **GitHub attestation verification rejected it**;
- the valid archive was verified under `octocat/Hello-World`: **repository trust policy rejected it**;
- the verified JSON record was altered to report a wrong workflow name: **the local admission-policy parser rejected it**.

Status: `V30_NEGATIVE_ADMISSION_TESTS_PASS`, **3/3 rejected**.

The unit suite also rejects wrong subject digests, archive path traversal, archive links and raw-source-data members.

## Interpretation boundary

Artifact attestation and release admission answer a supply-chain question: *is this exact archive traceable to an expected GitHub build identity, and does it contain the expected integrity-verified shadow bundle?*

They do **not** answer whether the model is statistically better, safe for customers or approved for pricing. Those remain separate model-risk/governance questions. v0.30 therefore deliberately returns `ADMIT_TO_SHADOW_REGISTRY_ONLY`, not `PROMOTE`, `DEPLOY_TO_PRICING` or any equivalent production decision.
