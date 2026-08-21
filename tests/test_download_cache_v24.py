from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from download_spanish_motor_2022_2024 import VERIFIED_FILES, verified_cache_hit


class TestVerifiedSourceCacheV24(unittest.TestCase):
    def test_cache_hit_requires_size_and_sha256(self) -> None:
        name = "v24_test_source.csv"
        payload = b"verified-cache-fixture"
        VERIFIED_FILES[name] = {
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixture.csv"
                path.write_bytes(payload)
                hit, digest = verified_cache_hit(path, name, len(payload))
                self.assertTrue(hit)
                self.assertEqual(digest, VERIFIED_FILES[name]["sha256"])

                path.write_bytes(payload + b"changed")
                hit, digest = verified_cache_hit(path, name, len(payload))
                self.assertFalse(hit)
                self.assertIsNone(digest)
        finally:
            VERIFIED_FILES.pop(name, None)

    def test_metadata_size_change_fails_closed(self) -> None:
        name = "v24_test_metadata.csv"
        payload = b"metadata-fixture"
        VERIFIED_FILES[name] = {
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixture.csv"
                path.write_bytes(payload)
                with self.assertRaises(RuntimeError):
                    verified_cache_hit(path, name, len(payload) + 1)
        finally:
            VERIFIED_FILES.pop(name, None)


if __name__ == "__main__":
    unittest.main()
