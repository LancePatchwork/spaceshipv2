import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(tmp_path: Path, *args: str) -> list[dict[str, object]]:
    env = os.environ.copy()
    env["EVT_STATE_FILE"] = str(tmp_path / "state.pkl")
    # ensure engine package is importable when running tools/ scripts
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run(
        [sys.executable, "tools/evt.py", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def test_cli_smoke(tmp_path: Path) -> None:
    run_cli(tmp_path, "spawn-red-alert", "--reason", "combat", "--auto-stations")
    run_cli(
        tmp_path,
        "subscribe",
        "--actor-id",
        "chief_engineer",
        "--scopes",
        "department:engineering",
        "--scopes",
        "officers",
    )
    list_out = run_cli(tmp_path, "list", "--actor-id", "chief_engineer")
    assert any(entry.get("events") for entry in list_out)
    claim_out = run_cli(tmp_path, "claim", "--actor-id", "chief_engineer")
    evt = claim_out[0]["evt"]
    assert isinstance(evt, dict) and evt.get("state") == "claimed"
