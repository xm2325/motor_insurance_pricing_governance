from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

DATASET_ID = "sw4jmdb2sm"
VERSION = 1
API_URL = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files?folder_id=root&version={VERSION}"


def main() -> None:
    outdir = Path("results_oot_2024")
    outdir.mkdir(parents=True, exist_ok=True)
    req = Request(API_URL, headers={"User-Agent": "motor-insurance-pricing-governance/0.13"})
    with urlopen(req, timeout=90) as response:
        files = json.load(response)

    compact = []
    for item in files:
        details = item.get("content_details") or {}
        compact.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "size": item.get("size"),
            "download_url": details.get("download_url"),
            "content_type": item.get("content_type"),
        })

    payload = {
        "status": "MENDELEY_FILE_DISCOVERY_OK",
        "dataset_id": DATASET_ID,
        "version": VERSION,
        "api_url": API_URL,
        "file_count": len(compact),
        "files": compact,
    }
    (outdir / "mendeley_files.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
