from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


def test_openapi_artifact_is_committed_and_current() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    artifact_path = repo_root / "docs" / "openapi" / "single-origin.openapi.json"

    assert artifact_path.exists(), "OpenAPI artifact missing. Run scripts/export-openapi.py"

    committed = artifact_path.read_text(encoding="utf-8")
    generated = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"

    assert committed == generated, "OpenAPI artifact drift detected. Run scripts/export-openapi.py"
