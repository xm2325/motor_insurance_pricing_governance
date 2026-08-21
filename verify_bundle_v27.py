from __future__ import annotations

import argparse
import json
from pathlib import Path

from deployment.provenance import verify_bundle_lock


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the v0.27 content-addressed deployment bundle before serving."
    )
    parser.add_argument("bundle", nargs="?", default="deployment_artifacts")
    args = parser.parse_args()

    report = verify_bundle_lock(Path(args.bundle))
    print(json.dumps(report.as_dict(), indent=2))


if __name__ == "__main__":
    main()
