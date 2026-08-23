"""Fail-closed model-change committee readiness gate for v0.44.

This module evaluates whether a change request may advance to a *human* review.
It never authorises model promotion or customer pricing.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List


READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_COMMITTEE_REVIEW"
EVIDENCE_GAP_HOLD = "EVIDENCE_GAP_HOLD"


@dataclass(frozen=True)
class GateInput:
    gate_id: str
    passed: bool
    evidence: str
    required: bool = True


@dataclass(frozen=True)
class CommitteeDecision:
    request_id: str
    status: str
    gate_results: List[dict]
    blocker_ids: List[str]
    required_gate_count: int
    required_gate_pass_count: int
    human_committee_review_open: bool
    automatic_model_promotion_authorised: bool
    automatic_customer_pricing_change_authorised: bool
    human_signoff_recorded: bool
    human_signoff_can_override_failed_evidence_gate: bool


def evaluate_change_request(
    request_id: str,
    gates: Iterable[GateInput],
    *,
    human_signoff_recorded: bool = False,
) -> CommitteeDecision:
    """Evaluate readiness without allowing a human flag to bypass failed evidence.

    `human_signoff_recorded` is audit metadata only. Even if True, failed required
    evidence gates keep the request on HOLD. Passing all machine gates advances
    only to human review; it never performs promotion.
    """

    gate_list = list(gates)
    if not gate_list:
        raise ValueError("At least one gate is required")
    ids = [g.gate_id for g in gate_list]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate gate ids are not allowed")

    required = [g for g in gate_list if g.required]
    blockers = [g.gate_id for g in required if not g.passed]
    status = READY_FOR_HUMAN_REVIEW if not blockers else EVIDENCE_GAP_HOLD

    results = []
    for gate in gate_list:
        row = asdict(gate)
        row["status"] = "PASS" if gate.passed else "FAIL"
        results.append(row)

    return CommitteeDecision(
        request_id=request_id,
        status=status,
        gate_results=results,
        blocker_ids=blockers,
        required_gate_count=len(required),
        required_gate_pass_count=sum(g.passed for g in required),
        human_committee_review_open=(status == READY_FOR_HUMAN_REVIEW),
        automatic_model_promotion_authorised=False,
        automatic_customer_pricing_change_authorised=False,
        human_signoff_recorded=human_signoff_recorded,
        human_signoff_can_override_failed_evidence_gate=False,
    )


def gate_map(decision: CommitteeDecision) -> Dict[str, dict]:
    return {row["gate_id"]: row for row in decision.gate_results}
