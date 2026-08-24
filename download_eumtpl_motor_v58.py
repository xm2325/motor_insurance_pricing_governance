from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

PREREG = Path("governance/external_temporal_prereg_v57.json")
V57_LOCK = Path("action_results/v57/eumtpl_external_temporal_prereg_lock.json")
V57_STATUS = Path("action_results/v57/ACTION_V57_STATUS.json")
OUTDIR = Path("data_external_v58")
AUDIT_DIR = Path("results_v58")
DATA_PATH = OUTDIR / "euMTPL.rda"
EXPECTED_PROTOCOL_SHA256 = "a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5"
EXPECTED_V57_MAIN_SHA = "cacb55a039c6132b7c2466f6356903250dc624d3"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    h = hashlib.sha1()
    h.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    lock = json.loads(V57_LOCK.read_text(encoding="utf-8"))
    status = json.loads(V57_STATUS.read_text(encoding="utf-8"))
    actual_protocol_sha = sha256_file(PREREG)
    if actual_protocol_sha != EXPECTED_PROTOCOL_SHA256 or lock["protocol_sha256"] != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("v0.57 protocol digest changed before v0.58 execution")
    if status["status"] != "success" or status["sha"] != EXPECTED_V57_MAIN_SHA:
        raise RuntimeError("v0.57 main preregistration lock is not the registered source")
    if status["row_level_external_data_accessed"] is not False or status["outcomes_inspected"] is not False:
        raise RuntimeError("v0.57 no-data preregistration evidence changed")
    if status["future_row_level_execution_allowed_only_in_v58_or_later"] is not True:
        raise RuntimeError("v0.57 does not authorise the registered future execution")

    source = prereg["source"]
    commit = source["upstream_commit"]
    upstream_path = source["upstream_path"]
    url = f"https://raw.githubusercontent.com/{source['upstream_repository']}/{commit}/{upstream_path}"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, DATA_PATH)

    actual_size = DATA_PATH.stat().st_size
    actual_git_blob = git_blob_sha1(DATA_PATH)
    if actual_size != int(source["upstream_blob_size_bytes"]):
        raise RuntimeError(f"euMTPL byte size changed: {actual_size}")
    if actual_git_blob != source["upstream_git_blob_sha"]:
        raise RuntimeError(f"euMTPL Git blob identity changed: {actual_git_blob}")

    audit = {
        "status": "V58_PINNED_EUMTPL_BINARY_VERIFIED_BEFORE_DECODE",
        "v57_protocol_sha256": actual_protocol_sha,
        "v57_main_sha": status["sha"],
        "source_repository": source["upstream_repository"],
        "source_commit": commit,
        "source_path": upstream_path,
        "download_url": url,
        "file_name": DATA_PATH.name,
        "file_bytes": actual_size,
        "git_blob_sha1": actual_git_blob,
        "file_sha256": sha256_file(DATA_PATH),
        "binary_downloaded": True,
        "decoded_in_downloader": False,
        "row_outcomes_inspected_in_downloader": False,
        "raw_data_persisted_to_repository": False
    }
    (AUDIT_DIR / "eumtpl_source_binary_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
