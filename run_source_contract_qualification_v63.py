from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

import pyreadr

POLICY = Path("governance/source_contract_qualification_policy_v63.json")
OUTDIR = Path("results_v63")
TEMPDIR = Path("/tmp/source_qualification_v63")
UPSTREAM_REPO = "dutangc/CASdatasets"
UPSTREAM_COMMIT = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"


def git_blob_sha1_bytes(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode("ascii"))
    h.update(data)
    return h.hexdigest()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def documentation_identifiers(text: str) -> set[str]:
    # Identifier tokens only. Numeric/example values are deliberately ignored.
    return set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", text))


def normalise_list_objects(raw: Any) -> dict[str, list[str] | None]:
    if isinstance(raw, dict):
        result: dict[str, list[str] | None] = {}
        for name, columns in raw.items():
            if columns is None:
                result[str(name)] = None
            else:
                result[str(name)] = [str(x) for x in columns]
        return result
    if isinstance(raw, list):
        result = {}
        for item in raw:
            if not isinstance(item, dict):
                raise RuntimeError(f"Unsupported pyreadr.list_objects item: {type(item)!r}")
            name = item.get("object_name", item.get("object", item.get("name")))
            columns = item.get("columns", item.get("column_names"))
            if name is None:
                raise RuntimeError(f"Cannot identify object name from list_objects item: {item}")
            result[str(name)] = None if columns is None else [str(x) for x in columns]
        return result
    raise RuntimeError(f"Unsupported pyreadr.list_objects return type: {type(raw)!r}")


def fetch_bytes(path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_COMMIT}/{path}"
    with urllib.request.urlopen(url) as response:
        return response.read()


def near_matches(left: list[str], right: list[str], max_distance: int) -> list[dict[str, Any]]:
    matches = []
    for a in left:
        candidates = sorted((levenshtein(a, b), b) for b in right)
        if candidates and candidates[0][0] <= max_distance:
            matches.append({"left": a, "right": candidates[0][1], "distance": candidates[0][0]})
    return matches


def qualify_case(case: dict[str, Any], max_distance: int) -> dict[str, Any]:
    source_bytes = fetch_bytes(case["source_path"])
    if len(source_bytes) != case["source_bytes"]:
        raise RuntimeError(f"{case['case_id']}: source byte size changed")
    if git_blob_sha1_bytes(source_bytes) != case["source_git_blob_sha1"]:
        raise RuntimeError(f"{case['case_id']}: source Git blob changed")

    docs_bytes = fetch_bytes(case["documentation_path"])
    if git_blob_sha1_bytes(docs_bytes) != case["documentation_git_blob_sha1"]:
        raise RuntimeError(f"{case['case_id']}: documentation Git blob changed")
    docs_text = docs_bytes.decode("utf-8")
    doc_ids = documentation_identifiers(docs_text)

    TEMPDIR.mkdir(parents=True, exist_ok=True)
    local_path = TEMPDIR / f"{case['case_id']}.rda"
    local_path.write_bytes(source_bytes)

    # Critical Q0 boundary: schema metadata only. Never replace this with value decoding.
    object_map = normalise_list_objects(pyreadr.list_objects(str(local_path)))
    if case["object_name"] not in object_map:
        decision = "SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL"
        columns: list[str] = []
        object_missing = True
    else:
        columns = object_map[case["object_name"]] or []
        object_missing = object_map[case["object_name"]] is None
        decision = "PENDING"

    proposed = list(case["proposed_required_columns"])
    proposed_set = set(proposed)
    binary_set = set(columns)
    registered_only = sorted(proposed_set - binary_set)
    binary_only = sorted(binary_set - proposed_set)
    schema_near = near_matches(registered_only, binary_only, max_distance)

    binary_not_documented = sorted(binary_set - doc_ids)
    documented_not_binary = sorted((set(proposed) & doc_ids) - binary_set)
    docs_near = near_matches(binary_not_documented, sorted(doc_ids), max_distance)

    if object_missing or registered_only or binary_only:
        decision = "SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL"
    elif any(name not in doc_ids for name in proposed):
        decision = "SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL"
    else:
        decision = "QUALIFIED_FOR_PROSPECTIVE_SEAL_NOT_YET_VALIDATION"

    output = {
        "case_id": case["case_id"],
        "historical_dataset": case["dataset"],
        "historical_only_not_a_new_evidence_stage": True,
        "source_identity": {
            "repository": UPSTREAM_REPO,
            "commit": UPSTREAM_COMMIT,
            "path": case["source_path"],
            "bytes": len(source_bytes),
            "git_blob_sha1": git_blob_sha1_bytes(source_bytes),
        },
        "documentation_identity": {
            "path": case["documentation_path"],
            "bytes": len(docs_bytes),
            "git_blob_sha1": git_blob_sha1_bytes(docs_bytes),
        },
        "metadata_access": {
            "api": "pyreadr.list_objects",
            "object_names": sorted(object_map),
            "selected_object": case["object_name"],
            "column_names": columns,
            "row_values_accessed": False,
            "outcome_values_accessed": False,
            "exposure_values_accessed": False,
            "feature_values_accessed": False,
            "row_count_computed_from_data": False,
            "pyreadr_read_r_called": False,
        },
        "comparison": {
            "proposed_required_columns": proposed,
            "registered_only_columns": registered_only,
            "binary_only_columns": binary_only,
            "schema_near_matches": schema_near,
            "binary_columns_absent_from_documentation_identifiers": binary_not_documented,
            "proposed_documented_columns_absent_from_binary": documented_not_binary,
            "documentation_near_matches_for_binary_only_identifiers": docs_near,
            "column_order_ignored": True,
            "automatic_aliasing_used": False,
        },
        "qualification_decision": decision,
        "expected_retrospective_decision": case["expected_retrospective_decision"],
        "historical_terminal_state_is_not_modified": True,
    }
    output["qualification_sha256"] = sha256_json(output)
    return output


def main() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    max_distance = int(policy["near_match_rule"]["maximum_distance_for_review"])
    cases = [
        {
            "case_id": "V61_S1_PG15TRAINING_RETROSPECTIVE",
            "dataset": "pg15training",
            "object_name": "pg15training",
            "source_path": "data/pg15training.rda",
            "source_git_blob_sha1": "9e670d214c05a7454d558ab32de5df96a6b0aba6",
            "source_bytes": 1934161,
            "documentation_path": "man-md/pg15training.md",
            "documentation_git_blob_sha1": "9c0f44bd6bc2b24c760917398c6c0783b916d1f5",
            "proposed_required_columns": [
                "PolNum", "CalYear", "Gender", "Type", "Category", "Occupation", "Age", "Group1", "Bonus", "Poldur",
                "Value", "Adind", "SubGroup2", "Group2", "Density", "Expdays", "Numtppd", "Numtpbi", "Indtppd", "Indtpbi"
            ],
            "expected_retrospective_decision": "SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL",
        },
        {
            "case_id": "V57_EUMTPL_RETROSPECTIVE",
            "dataset": "euMTPL",
            "object_name": "euMTPL",
            "source_path": "data/euMTPL.rda",
            "source_git_blob_sha1": "4bb386d89606eb5b529206d0835e11074103042b",
            "source_bytes": 17829164,
            "documentation_path": "man-md/euMTPL.md",
            "documentation_git_blob_sha1": "c50e96b2a4a470edb000fd71de0f2f01334799c7",
            "proposed_required_columns": [
                "policy_id", "year", "group", "fuel_type", "vehicle_category", "vehicle_use", "province", "horsepower", "gender",
                "age", "exposure", "cost_nc", "num_nc", "cost_cg", "num_cg", "cost_cd", "num_cd", "cost_fcd", "num_fcd"
            ],
            "expected_retrospective_decision": "SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL",
        },
    ]

    results = [qualify_case(case, max_distance) for case in cases]
    for result in results:
        if result["qualification_decision"] != result["expected_retrospective_decision"]:
            raise RuntimeError(f"Historical Q0 diagnostic did not reproduce expected block: {result['case_id']}")

    summary = {
        "status": "V63_METADATA_ONLY_SOURCE_CONTRACT_QUALIFICATION_REPLAY_PASS",
        "policy_status": policy["status"],
        "cases": results,
        "new_fresh_source_opened": False,
        "new_change_request_created": False,
        "row_values_accessed": False,
        "outcome_values_accessed": False,
        "model_fit_executed": False,
        "performance_metrics_computed": False,
        "mcr_001_reopened": False,
        "mcr_002_reopened": False,
        "historical_committee_gate_pass_count": 5,
        "historical_committee_gate_count": 8,
        "historical_model_family_decision": "HOLD",
        "historical_serving_status": "HOLD_SHADOW_ONLY",
        "historical_promotion_review_status": "NOT_OPEN",
        "customer_pricing_authorised": False,
    }
    summary["summary_sha256"] = sha256_json(summary)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "source_contract_qualification_replay_v63.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
