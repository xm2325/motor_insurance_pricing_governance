from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUSH_HELPER = ROOT / "scripts" / "push_evidence_with_rebase.sh"
V30 = ROOT / ".github" / "workflows" / "v30-admission.yml"
V31 = ROOT / ".github" / "workflows" / "v31-outcome-review.yml"


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def configure_identity(cwd: Path) -> None:
    git(cwd, "config", "user.name", "CI Test")
    git(cwd, "config", "user.email", "ci-test@example.invalid")


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

    def test_detached_evidence_commit_survives_concurrent_main_advance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote = root / "remote.git"
            seed = root / "seed"
            runner = root / "runner"
            verify = root / "verify"

            subprocess.run(
                ["git", "init", "--bare", str(remote)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                ["git", "clone", str(remote), str(seed)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            configure_identity(seed)
            git(seed, "checkout", "-b", "main")
            (seed / "base.txt").write_text("base\n", encoding="utf-8")
            git(seed, "add", "base.txt")
            git(seed, "commit", "-m", "base")
            git(seed, "push", "-u", "origin", "main")
            base_sha = git(seed, "rev-parse", "HEAD")

            subprocess.run(
                ["git", "clone", str(remote), str(runner)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            configure_identity(runner)
            git(runner, "checkout", "--detach", base_sha)
            (runner / "evidence.json").write_text('{"status":"success"}\n', encoding="utf-8")
            git(runner, "add", "evidence.json")
            git(runner, "commit", "-m", "evidence")

            (seed / "ci-status.json").write_text('{"ci":"success"}\n', encoding="utf-8")
            git(seed, "add", "ci-status.json")
            git(seed, "commit", "-m", "concurrent ci status")
            git(seed, "push", "origin", "main")

            subprocess.run(
                ["bash", str(PUSH_HELPER), "main", "3"],
                cwd=runner,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            subprocess.run(
                ["git", "clone", "--branch", "main", str(remote), str(verify)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertTrue((verify / "base.txt").is_file())
            self.assertTrue((verify / "ci-status.json").is_file())
            self.assertTrue((verify / "evidence.json").is_file())
            self.assertEqual(git(verify, "rev-list", "--count", "HEAD"), "3")


if __name__ == "__main__":
    unittest.main()
