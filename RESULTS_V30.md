# v0.30 — Runtime SBOM, Vulnerability Gate and SBOM Attestation

## Decision

**PASS for the v0.30 shadow-runtime supply-chain gate. Model governance remains `HOLD / HOLD_SHADOW_ONLY`.**

v0.30 does not change the pricing models or approve them for customer pricing. It adds build-time evidence about what is inside the CPU runtime image, which HIGH/CRITICAL vulnerabilities the scanner sees, which findings must be remediated, and which unpatched CRITICAL findings have a narrow time-limited exploitability review.

## Why this version was added

v0.29 gave the sealed release archive cryptographically verifiable GitHub/Sigstore build provenance. That answers **who/what workflow produced a specific artifact digest**, but it does not answer **what dependencies are inside the runtime image** or **whether known vulnerable packages are present at build time**.

v0.30 therefore adds:

1. a CycloneDX SBOM generated from the actual CPU-only Docker image;
2. a HIGH/CRITICAL Trivy scan of that same image;
3. a pre-specified security policy;
4. remediation of published Debian fixes before runtime installation;
5. an explicit expiring VEX review for CRITICAL findings that currently have no stable Debian fix and are not reachable in this service configuration;
6. the existing content-addressed bundle and same-fit scoring parity gates;
7. a GitHub/Sigstore SBOM attestation for the runtime image archive and an immediate `gh attestation verify` check.

Both `aquasecurity/trivy-action` invocations are pinned to immutable commit `ed142fd0673e97e23eac54620cfb913e5ce36c25` (v0.36.0). `actions/attest` remains pinned to immutable commit `508db95dd578ae2727ebd6217d5ba78e4fbda05d` (v4.2.1).

## First pass: strict gate failed

The first v0.30 run intentionally used the existing `python:3.12-slim` runtime without changing the security policy after seeing the scan.

GitHub Actions run: `32586229334`  
Artifact: `9479131884`  
Artifact digest: `sha256:ed43f07cc39ca1e04ca6e59e10aed0a19b692d20b3b4fc27e11b5f02c4fc0d61`

The scan found:

| First-pass finding | Count |
|---|---:|
| HIGH | 50 |
| HIGH with published fix | **36** |
| HIGH without published fix | 14 |
| CRITICAL | 3 |
| CRITICAL with published fix | 0 |

The build failed at policy enforcement as designed. The 36 fixable HIGH findings were in Debian util-linux-family packages with an available stable update. The three CRITICAL findings were in `perl-base` and did not have a stable fix in the scanned Debian base at the time of the run.

The immutable first-pass summary is retained in `security/v30_first_pass_failure.json` so the final PASS cannot hide the failed initial gate.

## Remediation

The runtime Dockerfile now runs the Debian package upgrade before installing the Python serving stack. The policy was **not** weakened for fixable findings:

- any CRITICAL finding with a published fixed version fails;
- any HIGH finding with a published fixed version fails;
- an unpatched CRITICAL finding fails unless it has a CVE/package-specific, non-expired `not_affected` VEX statement with a substantive reason;
- unpatched HIGH findings are recorded for review, but do not fail this demonstration gate;
- the VEX expires on **2026-09-30**, so it cannot silently become permanent.

The VEX currently covers exactly three `perl-base` findings and includes the corresponding Debian security-tracker source for each statement:

- `CVE-2026-13221` — vulnerable Perl regex path is not executed by the Python/FastAPI shadow service;
- `CVE-2026-42496` — Perl `Archive::Tar` extraction path is not used and user-supplied archives are not extracted;
- `CVE-2026-8376` — the affected 32-bit build condition does not match the validated `linux/amd64` runtime.

If Debian publishes a fixed version for any CRITICAL finding, VEX is no longer sufficient and the build fails until the runtime is updated. If the VEX expires, the build also fails.

## Verified final result

The final successful branch-push workflow persisted evidence under `action_results/v30/` for code SHA `5f1b23ba9c67818976e5ddfea43f9df7b7f404b9`.

| v0.30 result | Verified value |
|---|---:|
| Runtime architecture | `amd64` |
| Runtime image size | **495,953,375 bytes** |
| CycloneDX components | **112** |
| HIGH total | **14** |
| HIGH with published fix | **0** |
| Unfixed HIGH recorded | **14** |
| CRITICAL total | **3** |
| CRITICAL with published fix | **0** |
| CRITICAL covered by non-expired VEX | **3** |
| Unreviewed CRITICAL | **0** |
| VEX expiry | **2026-09-30** |
| Same-fit HTTP comparisons | **25 records × 4 fields = 100** |
| Max absolute HTTP parity error | **0.0** |
| SBOM attestation verification | **PASS** |
| GitHub SBOM attestation ID | **42340101** |

The important remediation result is:

`fixable HIGH: 36 -> 0`

The remaining 14 HIGH findings have no fixed version in the scanned image according to the build-time Trivy data. They remain visible in the scan evidence; they are not re-labelled as safe.

## SBOM and provenance

The final persisted build recorded:

- runtime archive SHA-256: `8e8ec563fb80c85eeb1a662260edbcc06811f16ffc4b02457b7f07fb02ac14f3`;
- CycloneDX SBOM SHA-256: `e9a4cec2da3c5a197b38b15dfe819c5340df608d51918b31fcd51899366d7a3d`;
- GitHub SBOM attestation ID: `42340101`;
- immediate `gh attestation verify` success;
- no `pytest`, `matplotlib`, `httpx`, `tabulate` or NVIDIA NCCL package in the runtime SBOM;
- `xgboost-cpu` remains the XGBoost runtime component;
- raw Mendeley source data is not copied into the runtime image.

The SBOM attestation binds the CycloneDX document to the exact runtime image archive subject through GitHub Actions OIDC/Sigstore provenance. It does not mean the image is permanently vulnerability-free.

## Model behaviour did not change

After the Debian security update, VEX/security controls and immutable action pinning, the container still loaded the integrity-verified v0.27 hybrid bundle and reproduced the same-fit shadow scores:

`100 / 100 comparisons passed; max absolute error = 0.0`.

This is important because a runtime security remediation is not accepted merely because the scanner becomes greener; the existing model-serving contract must remain unchanged.

## Boundaries

- Trivy results are a build-time view of the vulnerability database, not a permanent security guarantee.
- The three VEX statements are narrow, time-limited exploitability reviews, not a blanket CVE ignore list.
- The project flag/rationale is not a substitute for an insurer's security, IAM, change-approval or vulnerability-management process.
- v0.30 is a shadow-runtime supply-chain control. It does not establish production readiness, regulatory approval or transport to FIRST CENTRAL / the UK motor market.
- Model-family status remains **HOLD** and serving remains **HOLD_SHADOW_ONLY**.

## Evidence

- `action_results/v30/runtime_supply_chain_result.json`
- `action_results/v30/supply_chain_policy_result.json`
- `action_results/v30/runtime_http_parity.json`
- `action_results/v30/sbom_attestation_verification.json`
- `action_results/v30/vex_v30.json`
- `security/v30_first_pass_failure.json`
- `security/vex_v30.json`
- `tests/test_supply_chain_v30.py`
- `tests/test_supply_chain_evidence_v30.py`
