from __future__ import annotations

import json
from pathlib import Path

import pyreadr
from pyreadr._pyreadr_parser import ListObjectsParser


def _discard_row_name(self, name, index):
    # pyreadr.list_objects is intended to return only object/column names.
    # librdata nevertheless emits a row-name callback for these RDA files.
    # Discard it immediately: do not store, compare, count or persist row names.
    return None


def install_metadata_only_patch() -> dict:
    missing_before = not hasattr(ListObjectsParser, "handle_row_name")
    if missing_before:
        ListObjectsParser.handle_row_name = _discard_row_name
    return {
        "pyreadr_version": getattr(pyreadr, "__version__", "unknown"),
        "parser": "ListObjectsParser",
        "missing_handle_row_name_before_patch": missing_before,
        "patch": "no-op handle_row_name callback",
        "row_names_stored": False,
        "row_names_compared": False,
        "row_names_persisted": False,
        "column_values_callback_added": False,
        "value_decode_api_used": False,
        "reason": "pyreadr 0.5.3 and 0.5.6 list_objects fail on these RDA files because ListObjectsParser lacks the row-name callback expected by librdata",
    }


def main() -> None:
    patch = install_metadata_only_patch()
    import run_source_contract_qualification_v63 as replay

    replay.main()
    out = Path("results_v63")
    out.mkdir(parents=True, exist_ok=True)
    (out / "metadata_reader_patch_v63.json").write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(patch, indent=2))


if __name__ == "__main__":
    main()
