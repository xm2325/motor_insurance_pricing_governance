from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

DATASET_ID = "sw4jmdb2sm"
VERSION = 1
API_URL = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}/files?folder_id=root&version={VERSION}"

VERIFIED_FILES = {
    "Dataset of motor insurance portfolio.csv": {
        "size": 94710312,
        "sha256": "6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4",
    },
    "Descriptive of variables.xlsx": {
        "size": 15413,
        "sha256": "cde44e797a7fd34de29199c78c9301d6f00ed94fd725b4fe8e67e6c2c4cc2e41",
    },
}


def safe_name(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    value = value.strip().strip('"')
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value or fallback


def filename_from_disposition(header: str | None) -> str | None:
    if not header:
        return None
    match = re.search(r"filename\*=UTF-8''([^;]+)", header, flags=re.I)
    if match:
        from urllib.parse import unquote
        return unquote(match.group(1))
    match = re.search(r'filename="?([^";]+)"?', header, flags=re.I)
    return match.group(1).strip() if match else None


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_cache_hit(path: Path, api_name: str | None, api_size: int | None) -> tuple[bool, str | None]:
    """Accept a cached source only when versioned metadata, size and SHA-256 all match."""
    if not path.exists() or not api_name or api_name not in VERIFIED_FILES:
        return False, None
    expected = VERIFIED_FILES[api_name]
    expected_size = int(expected["size"])
    if api_size is not None and int(api_size) != expected_size:
        raise RuntimeError(
            f"Mendeley metadata changed for {api_name}: {api_size} != verified {expected_size}"
        )
    if path.stat().st_size != expected_size:
        return False, None
    digest = sha256_path(path)
    return digest == expected["sha256"], digest


def classify(path: Path) -> dict:
    head = path.read_bytes()[:64]
    info: dict = {"first_32_bytes_hex": head[:32].hex()}
    if head.startswith(b"PK"):
        info["container"] = "zip"
        try:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                info["zip_member_count"] = len(names)
                info["zip_members_preview"] = names[:25]
                info["looks_like_xlsx"] = "[Content_Types].xml" in names and any(
                    n.startswith("xl/") for n in names
                )
        except Exception as exc:
            info["zip_error"] = repr(exc)
    elif head.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        info["container"] = "ole_compound_binary"
        info["looks_like_xls"] = True
    else:
        info["container"] = "text_or_other"
        try:
            info["text_preview"] = path.read_bytes()[:500].decode("utf-8", errors="replace")
        except Exception as exc:
            info["text_preview_error"] = repr(exc)
    return info


def main() -> None:
    data_dir = Path("data_spanish_2022_2024")
    outdir = Path("results_oot_2024")
    data_dir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)

    req = Request(API_URL, headers={"User-Agent": "motor-insurance-pricing-governance/0.24"})
    with urlopen(req, timeout=90) as response:
        files = json.load(response)

    audit_files = []
    for index, item in enumerate(files, start=1):
        details = item.get("content_details") or {}
        url = details.get("download_url")
        if not url:
            raise RuntimeError(f"Mendeley file lacks download_url: {item}")
        file_id = str(item.get("id") or f"file_{index}")
        api_name = item.get("filename") or item.get("name") or details.get("filename")
        api_size = item.get("size")
        local_name = safe_name(api_name, f"{file_id}.bin")
        local_path = data_dir / local_name

        cache_hit, cached_digest = verified_cache_hit(local_path, api_name, api_size)
        disposition = None
        content_type = None
        reported_length = None

        if cache_hit:
            nbytes = local_path.stat().st_size
            digest_hex = cached_digest
            source_mode = "VERIFIED_CACHE_HIT"
        else:
            request = Request(url, headers={"User-Agent": "motor-insurance-pricing-governance/0.24"})
            with urlopen(request, timeout=180) as response:
                disposition = response.headers.get("Content-Disposition")
                content_type = response.headers.get("Content-Type")
                reported_length = response.headers.get("Content-Length")
                header_name = filename_from_disposition(disposition)
                if header_name:
                    local_name = safe_name(header_name, local_name)
                    local_path = data_dir / local_name
                digest = hashlib.sha256()
                nbytes = 0
                with local_path.open("wb") as fh:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        digest.update(chunk)
                        nbytes += len(chunk)
                        fh.write(chunk)
            digest_hex = digest.hexdigest()
            source_mode = "NETWORK_DOWNLOAD"

        verified = VERIFIED_FILES.get(api_name or "")
        if verified:
            if nbytes != int(verified["size"]) or digest_hex != verified["sha256"]:
                raise RuntimeError(
                    f"Verified source mismatch for {api_name}: size={nbytes}, sha256={digest_hex}"
                )

        record = {
            "id": file_id,
            "api_keys": sorted(item.keys()),
            "api_filename": api_name,
            "content_disposition": disposition,
            "content_type": content_type,
            "reported_content_length": reported_length,
            "api_size": api_size,
            "downloaded_bytes": nbytes,
            "sha256": digest_hex,
            "local_filename": local_name,
            "source_mode": source_mode,
            "cache_hit": cache_hit,
        }
        record.update(classify(local_path))
        audit_files.append(record)

    payload = {
        "status": "MENDELEY_DOWNLOAD_AND_FORMAT_AUDIT_OK",
        "dataset_id": DATASET_ID,
        "version": VERSION,
        "cache_contract": "Reuse only after versioned size + SHA-256 verification",
        "files": audit_files,
    }
    (outdir / "download_format_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
