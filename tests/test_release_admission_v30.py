from __future__ import annotations

import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from verify_release_admission_v30 import (
    EXPECTED_REPOSITORY,
    EXPECTED_WORKFLOW_NAME,
    EXPECTED_WORKFLOW_PATH,
    _attestation_identity,
    _validate_archive_members,
)


ARCHIVE_NAME = "motor-pricing-shadow-bundle-v30.tar.gz"
ARCHIVE_SHA = "a" * 64


def verification_record(
    *,
    repository: str = EXPECTED_REPOSITORY,
    workflow_name: str = EXPECTED_WORKFLOW_NAME,
    workflow_path: str = EXPECTED_WORKFLOW_PATH,
    subject_sha: str = ARCHIVE_SHA,
    subject_name: str = ARCHIVE_NAME,
) -> dict:
    repository_url = f"https://github.com/{repository}"
    return {
        "verificationResult": {
            "signature": {
                "certificate": {
                    "githubWorkflowRepository": repository,
                    "githubWorkflowName": workflow_name,
                    "githubWorkflowRef": "refs/heads/chatgpt/v0.30-attested-release-admission",
                    "sourceRepositoryDigest": "1" * 40,
                    "sourceRepositoryVisibilityAtSigning": "public",
                    "runnerEnvironment": "github-hosted",
                }
            },
            "verifiedTimestamps": [{"type": "Tlog"}],
            "statement": {
                "subject": [
                    {"name": subject_name, "digest": {"sha256": subject_sha}}
                ],
                "predicateType": "https://slsa.dev/provenance/v1",
                "predicate": {
                    "buildDefinition": {
                        "buildType": "https://actions.github.io/buildtypes/workflow/v1",
                        "externalParameters": {
                            "workflow": {
                                "path": workflow_path,
                                "ref": "refs/heads/chatgpt/v0.30-attested-release-admission",
                                "repository": repository_url,
                            }
                        },
                    }
                },
            },
        }
    }


class TestAttestedReleaseAdmissionV30(unittest.TestCase):
    def test_exact_subject_repo_and_workflow_are_accepted(self) -> None:
        identity = _attestation_identity(
            [verification_record()],
            archive_name=ARCHIVE_NAME,
            archive_sha256=ARCHIVE_SHA,
            expected_repository=EXPECTED_REPOSITORY,
            expected_workflow_name=EXPECTED_WORKFLOW_NAME,
            expected_workflow_path=EXPECTED_WORKFLOW_PATH,
        )
        self.assertEqual(identity["subject_sha256"], ARCHIVE_SHA)
        self.assertEqual(identity["repository"], EXPECTED_REPOSITORY)
        self.assertEqual(identity["workflow_name"], EXPECTED_WORKFLOW_NAME)
        self.assertEqual(identity["verified_timestamp_count"], 1)

    def test_wrong_repository_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "No verified attestation record"):
            _attestation_identity(
                [verification_record(repository="someone/else")],
                archive_name=ARCHIVE_NAME,
                archive_sha256=ARCHIVE_SHA,
                expected_repository=EXPECTED_REPOSITORY,
                expected_workflow_name=EXPECTED_WORKFLOW_NAME,
                expected_workflow_path=EXPECTED_WORKFLOW_PATH,
            )

    def test_wrong_workflow_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "No verified attestation record"):
            _attestation_identity(
                [verification_record(workflow_name="Wrong workflow")],
                archive_name=ARCHIVE_NAME,
                archive_sha256=ARCHIVE_SHA,
                expected_repository=EXPECTED_REPOSITORY,
                expected_workflow_name=EXPECTED_WORKFLOW_NAME,
                expected_workflow_path=EXPECTED_WORKFLOW_PATH,
            )

    def test_wrong_subject_digest_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "No verified attestation record"):
            _attestation_identity(
                [verification_record(subject_sha="b" * 64)],
                archive_name=ARCHIVE_NAME,
                archive_sha256=ARCHIVE_SHA,
                expected_repository=EXPECTED_REPOSITORY,
                expected_workflow_name=EXPECTED_WORKFLOW_NAME,
                expected_workflow_path=EXPECTED_WORKFLOW_PATH,
            )

    def test_archive_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                info = tarfile.TarInfo("../escape")
                payload = b"x"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with self.assertRaisesRegex(RuntimeError, "Unsafe archive member path"):
                _validate_archive_members(path)

    def test_archive_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-link.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                info = tarfile.TarInfo("deployment_artifacts/link")
                info.type = tarfile.SYMTYPE
                info.linkname = "/tmp/target"
                archive.addfile(info)
            with self.assertRaisesRegex(RuntimeError, "Archive links are not allowed"):
                _validate_archive_members(path)

    def test_raw_source_data_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-data.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                info = tarfile.TarInfo(
                    "deployment_artifacts/Dataset_of_motor_insurance_portfolio.csv"
                )
                payload = b"not-real-data"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with self.assertRaisesRegex(RuntimeError, "Raw source data token"):
                _validate_archive_members(path)


if __name__ == "__main__":
    unittest.main()
