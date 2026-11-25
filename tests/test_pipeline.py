"""Tests for the DVC pipeline stages (pipeline/*.py) and the helpers they use.
Each stage runs against a temporary copy of its inputs, so the repo is never modified."""

import json
import shutil

import pandas as pd
import pytest
import yaml

import amr_utils
import conftest
from pipeline import antibiogram, common, generate_data, validate
from pathlib import Path

ROOT = Path(conftest.ROOT)


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Point every stage at tmp_path (with copies of params.yaml and the GLASS table)."""
    (tmp_path / "data").mkdir()
    shutil.copy(ROOT / "data" / "glass_rates_pakistan_2023.csv", tmp_path / "data")
    shutil.copy(ROOT / "params.yaml", tmp_path / "params.yaml")
    paths = {
        "ROOT": tmp_path,
        "GLASS_CSV": tmp_path / "data" / "glass_rates_pakistan_2023.csv",
        "DEMO_CSV": tmp_path / "amr_data.csv",
        "OUTPUTS": tmp_path / "outputs",
        "METRICS": tmp_path / "metrics",
    }
    for module in (common, generate_data, antibiogram, validate):
        for name, value in paths.items():
            if hasattr(module, name):
                monkeypatch.setattr(module, name, value)
    return tmp_path


def test_generate_data_stage_reproduces_committed_csv_bytes(workdir):
    generate_data.main()
    assert (workdir / "amr_data.csv").read_bytes() == (ROOT / "amr_data.csv").read_bytes()


def test_generate_data_respects_params(workdir):
    params = yaml.safe_load((workdir / "params.yaml").read_text())
    params["data"]["n_rows"] = 50
    params["data"]["cities"] = ["Lahore", "Karachi"]
    (workdir / "params.yaml").write_text(yaml.safe_dump(params))
    generate_data.main()
    df = pd.read_csv(workdir / "amr_data.csv")
    assert len(df) == 50 and set(df["city"]) <= {"Lahore", "Karachi"}


def test_full_pipeline_outputs_and_metrics(workdir):
    generate_data.main()
    antibiogram.main()
    validate.main()

    for name in ["antibiogram_global.csv", "antibiogram_counts.csv",
                 "antibiogram_by_city.csv", "antibiogram_heatmap.png"]:
        assert (workdir / "outputs" / name).stat().st_size > 0, name

    abg = json.loads((workdir / "metrics" / "antibiogram.json").read_text())
    assert abg == {"n_isolates": 300, "n_pairs": 23, "pairs_below_min_isolates": 23,
                   "overall_resistance_rate": 46.7}

    val = json.loads((workdir / "metrics" / "validation.json").read_text())
    assert val["n_pairs"] == 23
    assert val["max_abs_diff_pair"] == "Klebsiella pneumoniae / Colistin"
    assert val["pairs_reference_inside_ci"] == 22

    plot = pd.read_csv(workdir / "metrics" / "demo_vs_who.csv")
    assert {"reference_rate", "observed_rate"} <= set(plot.columns)


def test_dvc_yaml_matches_stage_scripts():
    spec = yaml.safe_load((ROOT / "dvc.yaml").read_text())
    for name, stage in spec["stages"].items():
        module = stage["cmd"].split()[-1]                       # python -m pipeline.<x>
        assert (ROOT / (module.replace(".", "/") + ".py")).exists(), name
        for dep in stage["deps"]:
            assert (ROOT / dep).exists(), f"{name}: missing dep {dep}"
    params = yaml.safe_load((ROOT / "params.yaml").read_text())
    assert set(params) == {"data", "antibiogram"}


# ── helpers used by the validate stage ───────────────────────────────────────
def test_wilson_interval():
    assert amr_utils.wilson_interval(0, 0) == (0.0, 100.0)
    lo, hi = amr_utils.wilson_interval(5, 10)
    assert lo < 50 < hi and (lo, hi) == (23.7, 76.3)
    assert amr_utils.wilson_interval(0, 20)[0] == 0.0
    assert amr_utils.wilson_interval(20, 20)[1] == 100.0


def test_compare_with_reference():
    df = pd.DataFrame({
        "organism": ["A"] * 4 + ["B"] * 2,
        "antibiotic": ["x"] * 4 + ["y"] * 2,
        "result": ["Resistant", "Resistant", "Susceptible", "Susceptible", "Resistant", "Resistant"],
    })
    ref = pd.DataFrame({"organism": ["A", "B", "C"], "antibiotic": ["x", "y", "z"],
                        "percent_resistant": [50.0, 10.0, 99.0]})
    cmp = amr_utils.compare_with_reference(df, ref)
    assert cmp["organism"].tolist() == ["B", "A"]                # largest difference first
    assert cmp["observed_rate"].tolist() == [100.0, 50.0]
    assert cmp["abs_diff"].tolist() == [90.0, 0.0]
    assert cmp["reference_inside_ci"].tolist() == [False, True]
