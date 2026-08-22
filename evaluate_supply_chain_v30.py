from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_RUNTIME_PACKAGES = {
    "numpy": "2.5.2",
    "pandas": "3.0.5",
    "scipy": "1.18.0",
    "scikit-learn": "1.9.0",
    "joblib": "1.5.3",
}
REQUIRED_PRESENT = {"fastapi", "uvicorn"}
XGBOOST_ALIASES = {"xgboost", "xgboost-cpu"}
FORBIDDEN_RUNTIME_PACKAGES = {
    "httpx",
    "matplotlib",
    "nvidia-nccl-cu13",
    "pytest",
    "tabulate",
}


def normalise(name: str) -> str:
    return str(name).strip().lower().replace("_", "-")


def sbom_packages(sbom: dict[str, Any]) -> dict[str, str]:
    if sbom.get("bomFormat") != "CycloneDX":
        raise AssertionError(f"Expected CycloneDX SBOM, got {sbom.get('bomFormat')!r}")
    if not str(sbom.get("specVersion", "")).startswith("1."):
        raise AssertionError(f"Unexpected CycloneDX specVersion: {sbom.get('specVersion')!r}")
    components = sbom.get("components")
    if not isinstance(components, list) or len(components) < 10:
        raise AssertionError("Runtime SBOM must contain at least 10 components")
    result: dict[str, str] = {}
    for component in components:
        if not isinstance(component, dict):
            continue
        name = normalise(component.get("name", ""))
        version = str(component.get("version", ""))
        if name:
            result.setdefault(name, version)
    return result


def vulnerability_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in scan.get("Results") or []:
        if not isinstance(result, dict):
            continue
        target = result.get("Target")
        klass = result.get("Class")
        result_type = result.get("Type")
        for vuln in result.get("Vulnerabilities") or []:
            if not isinstance(vuln, dict):
                continue
            rows.append(
                {
                    "id": vuln.get("VulnerabilityID"),
                    "package": vuln.get("PkgName"),
                    "installed_version": vuln.get("InstalledVersion"),
                    "fixed_version": vuln.get("FixedVersion") or "",
                    "severity": str(vuln.get("Severity") or "UNKNOWN").upper(),
                    "target": target,
                    "class": klass,
                    "type": result_type,
                }
            )
    return rows


def evaluate(sbom: dict[str, Any], scan: dict[str, Any]) -> dict[str, Any]:
    packages = sbom_packages(sbom)

    missing_exact = {
        name: version
        for name, version in REQUIRED_RUNTIME_PACKAGES.items()
        if packages.get(name) != version
    }
    missing_present = sorted(name for name in REQUIRED_PRESENT if name not in packages)
    xgb_present = sorted(name for name in XGBOOST_ALIASES if name in packages)
    forbidden_present = sorted(FORBIDDEN_RUNTIME_PACKAGES.intersection(packages))

    if missing_exact:
        raise AssertionError(f"SBOM missing exact runtime packages: {missing_exact}")
    if missing_present:
        raise AssertionError(f"SBOM missing required runtime packages: {missing_present}")
    if not xgb_present:
        raise AssertionError("SBOM must contain xgboost or xgboost-cpu")
    if forbidden_present:
        raise AssertionError(f"Forbidden dev/GPU packages present in runtime SBOM: {forbidden_present}")

    rows = vulnerability_rows(scan)
    critical = [row for row in rows if row["severity"] == "CRITICAL"]
    high = [row for row in rows if row["severity"] == "HIGH"]
    fixable_high = [row for row in high if str(row["fixed_version"]).strip()]
    fixable_critical = [row for row in critical if str(row["fixed_version"]).strip()]

    policy_pass = len(critical) == 0 and len(fixable_high) == 0
    result = {
        "status": "V30_SUPPLY_CHAIN_POLICY_PASS" if policy_pass else "V30_SUPPLY_CHAIN_POLICY_FAIL",
        "sbom": {
            "format": sbom.get("bomFormat"),
            "spec_version": sbom.get("specVersion"),
            "component_count": len(sbom.get("components") or []),
            "required_exact_packages": REQUIRED_RUNTIME_PACKAGES,
            "xgboost_components": xgb_present,
            "forbidden_packages_present": forbidden_present,
        },
        "vulnerability_policy": {
            "policy": (
                "No CRITICAL vulnerabilities. No HIGH vulnerabilities when a fixed version is available. "
                "Unfixed HIGH findings are recorded for review but do not fail this demonstration gate."
            ),
            "high_total": len(high),
            "high_fixable": len(fixable_high),
            "critical_total": len(critical),
            "critical_fixable": len(fixable_critical),
            "high_unfixed": len(high) - len(fixable_high),
            "critical_findings": critical,
            "fixable_high_findings": fixable_high,
        },
        "governance_boundary": "HOLD / HOLD_SHADOW_ONLY remains unchanged",
        "security_boundary": (
            "This gate reports vulnerabilities visible to the scanner at build time. It is not a claim "
            "that the image is vulnerability-free, permanently secure, or approved for production pricing."
        ),
    }
    if not policy_pass:
        raise RuntimeError(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sbom = json.loads(args.sbom.read_text(encoding="utf-8"))
    scan = json.loads(args.scan.read_text(encoding="utf-8"))
    result = evaluate(sbom, scan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
