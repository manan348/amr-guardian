"""Paths and parameter loading shared by the pipeline stages."""

import json
from pathlib import Path

import yaml

ROOT        = Path(__file__).resolve().parent.parent
GLASS_CSV   = ROOT / "data" / "glass_rates_pakistan_2023.csv"
DEMO_CSV    = ROOT / "amr_data.csv"
OUTPUTS     = ROOT / "outputs"
METRICS     = ROOT / "metrics"


def load_params() -> dict:
    with open(ROOT / "params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": same bytes on Windows and Linux, so DVC hashes survive a git round-trip
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
