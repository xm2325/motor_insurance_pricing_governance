from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUSH_HELPER = ROOT / "scripts" / "push_evidence_with_rebase.sh"
V30 = ROOT / ".github" / "workflows" / "v30-admission.yml"
V31 = ROOT / ".github" / "workflows" / "v31-outcome-review.yml"


class EvidencePushStaticV31Tests(unittest.TestCase):
    def test_helper_rebases_and_uses_bounded_retry_without_force_push(self) -> None:
        source = PUSH_HELPER.read_text(encoding="utf-8")
        self.assertIn('MAX_ATTEMPTS="${2:-5}"', source)
        self.assertIn('git fetch origin "$TARGET_BRANCH"', source)
        self.assertIn('git rebase "origin/${TARGET_BRANCH}"', source)
        self.assertIn('git push origin "HEAD:${TARGET_BRANCH}"', source)
        self.assertIn('Evidence push failed after ${MAX_ATTEMPTS} attempts', source)
        self.assertNotIn("--force", source)
        self.assertNotIn("--force-with-lease", source)

    def test_v30_and_v31_use_race_safe_helper(self) -> None:
        for path in (V30, V31):
            workflow = path.read_text(encoding="utf-8")
            self.assertIn("scripts/push_evidence_with_rebase.sh", workflow)
            self.assertIn(
                'bash scripts/push_evidence_with_rebase.sh "$GITHUB_REF_NAME"',
                workflow,
            )
            self.assertNotIn("git push origin HEAD:${GITHUB_REF_NAME}", workflow)


if __name__ == "__main__":
    unittest.main()
