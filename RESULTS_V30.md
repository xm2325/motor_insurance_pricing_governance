# v0.30 — Runtime SBOM + Known-Vulnerability Gate

## Decision

**PASS — the exact CPU serving dependency set has a CycloneDX SBOM, a zero-known-vulnerability gate, and GitHub/Sigstore-backed SBOM provenance. Model governance remains `HOLD / HOLD_SHADOW_ONLY`.**

v0.30 changes dependency security evidence only. It does not change the pricing models, calibration, monitoring thresholds, release approval or customer-pricing behaviour.

## Verified run

GitHub Actions run `32525466315` built an isolated CPU runtime, froze the resolved application dependency set, audited that exact lock with `pip-audit 2.10.1`, generated a CycloneDX SBOM, rebuilt/sealed the shadow release, generated both build-provenance and SBOM attestations, and independently verified both with GitHub CLI.

| Check | Result |
|---|---:|
| Frozen application runtime distributions | **23** |
| `pip-audit` dependency records | **23** |
| CycloneDX components | **23** |
| Known vulnerabilities returned by `pip-audit` | **0** |
| CycloneDX spec version | **1.4** |
| Release archive | **386,607 bytes** |
| Release archive SHA-256 | `bbc7fd49dcd1ef05080afcfbb70e830dd9eb67ac66de4a3f9f2a9e311e194f45` |
| Build-provenance attestation ID | **42234539** |
| CycloneDX SBOM attestation ID | **42234544** |
| Provenance verification records | **1** |
| SBOM verification records | **1** |
| Governance | `HOLD_SHADOW_ONLY` |

Build provenance:

`https://github.com/xm2325/motor_insurance_pricing_governance/attestations/42234539`

CycloneDX SBOM attestation:

`https://github.com/xm2325/motor_insurance_pricing_governance/attestations/42234544`

## Runtime inventory boundary

The serving environment is created independently from the audit tool. Normal `pip freeze` captures the **23 deployable application distributions** and intentionally does not add the environment's own `pip` executable to the application dependency lock. `pip-audit` runs from a separate audit virtual environment, so `pip-audit` and its transitive packages do not contaminate the runtime SBOM.

The workflow has an explicit alignment gate:

`runtime lock count == pip-audit dependency count == CycloneDX component count == 23`

If the three inventories disagree, the release is rejected before attestation.

## Vulnerability gate

The exact frozen runtime lock is audited with `pip-audit 2.10.1` and `--no-deps`, because all entries in the generated lock are already pinned. The verified run returned **zero known vulnerability records**.

This gate is intentionally strict for this portfolio release: a non-zero `pip-audit` exit code or any reported vulnerability stops the release workflow. Vulnerabilities are not automatically ignored. A future finding should be investigated, fixed where possible, and followed by the relevant modelling/serving parity regression if the affected dependency can change model behaviour.

## CycloneDX SBOM attestation

The workflow generates a CycloneDX JSON SBOM and uses the immutable GitHub `actions/attest` v4.2.1 commit:

`508db95dd578ae2727ebd6217d5ba78e4fbda05d`

The SBOM is cryptographically associated with the exact sealed release archive using the recognised CycloneDX predicate type:

`https://cyclonedx.org/bom`

The workflow then verifies the SBOM attestation using:

`gh attestation verify ... --predicate-type https://cyclonedx.org/bom`

This is separate from the build-provenance attestation: one attestation describes **where/how the archive was built**, while the SBOM attestation binds the **runtime dependency inventory** to that same subject artifact.

## Interpretation boundary

`pip-audit` checks installed Python dependencies against known vulnerability data. A result of zero known vulnerabilities does **not** prove that the code is secure, that packages are non-malicious, that no unknown vulnerabilities exist, or that a reported vulnerability would be exploitable in this service.

The CycloneDX SBOM and GitHub attestation improve dependency transparency and verifiable provenance. They are not static analysis, penetration testing, malware detection, model validation, regulatory approval or permission to use the challenger for customer pricing.

The model-family decision therefore remains **HOLD**, and the service remains **HOLD_SHADOW_ONLY**.
