"""Unit tests for amr_utils — pure functions, no Streamlit, no network."""

import json
import os

import pandas as pd
import pytest

import amr_utils as u

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── normalize_result / clean_records ─────────────────────────────────────────
@pytest.mark.parametrize("raw, expected", [
    ("R", "Resistant"), ("r", "Resistant"), (" Resistant ", "Resistant"),
    ("S", "Susceptible"), ("Sensitive", "Susceptible"), ("susceptible", "Susceptible"),
    ("I", "Intermediate"), ("SDD", "Intermediate"), ("Intermediate", "Intermediate"),
])
def test_normalize_result_maps_known_codes(raw, expected):
    assert u.normalize_result(pd.Series([raw])).iloc[0] == expected


@pytest.mark.parametrize("raw", ["?", "maybe", "", None, "N/A"])
def test_normalize_result_unknown_becomes_nan(raw):
    assert pd.isna(u.normalize_result(pd.Series([raw])).iloc[0])


def test_clean_records_strips_parses_and_drops():
    raw = pd.DataFrame({
        "city": [" Lahore ", "Multan", "Quetta"],
        "organism": ["E. coli ", "E. coli", "E. coli"],
        "antibiotic": ["Cipro", " Meropenem", "Colistin"],
        "result": ["r", "?", "Sensitive"],
        "date": ["2024-01-01", "2024-01-02", "not a date"],
        "extra": [1, 2, 3],
    })
    clean, dropped = u.clean_records(raw)
    assert dropped == 1
    assert list(clean.columns) == u.RESULT_COLS
    assert clean["result"].tolist() == ["Resistant", "Susceptible"]
    assert clean["city"].tolist() == ["Lahore", "Quetta"]
    assert clean["date"].iloc[0] == pd.Timestamp("2024-01-01")
    assert pd.isna(clean["date"].iloc[1])           # bad date kept as NaT, not dropped
    assert clean.index.tolist() == [0, 1]


# ── standardize_columns ──────────────────────────────────────────────────────
def test_standardize_columns_aliases_and_bom():
    raw = pd.DataFrame(columns=["﻿Region", "Pathogen", "DRUG", "SIR",
                                "Collection_Date", "Unnamed: 0"])
    out = u.standardize_columns(raw)
    assert set(out.columns) == set(u.RESULT_COLS)
    assert u.missing_columns(out) == []


def test_standardize_columns_does_not_override_existing_standard_name():
    raw = pd.DataFrame(columns=["city", "region", "organism", "antibiotic", "result", "date"])
    out = u.standardize_columns(raw)
    assert "region" in out.columns and list(out.columns).count("city") == 1


def test_missing_columns_reports_what_is_absent():
    assert u.missing_columns(pd.DataFrame(columns=["city", "organism"])) == \
        ["antibiotic", "date", "result"]


# ── parse_llm_records ────────────────────────────────────────────────────────
TODAY = pd.Timestamp("2025-06-01")


def test_parse_llm_records_list_with_invalid_entry():
    text = "```json\n" + json.dumps([
        {"organism": "K. pneumoniae", "antibiotic": "Ceftriaxone", "result": "R",
         "city": "Lahore", "date": None},
        {"organism": "K. pneumoniae", "antibiotic": "Meropenem", "result": "S",
         "city": None, "date": "2024-03-15"},
        {"organism": "K. pneumoniae", "antibiotic": "X", "result": "maybe",
         "city": "Lahore", "date": "2024-03-15"},
    ]) + "\n```"
    df, dropped = u.parse_llm_records(text, today=TODAY)
    assert dropped == 1
    assert df["result"].tolist() == ["Resistant", "Susceptible"]
    assert df["date"].tolist() == [TODAY, pd.Timestamp("2024-03-15")]
    assert df["city"].tolist() == ["Lahore", "Unknown"]


def test_parse_llm_records_single_object():
    df, dropped = u.parse_llm_records(
        '{"organism": "E. coli", "antibiotic": "Cipro", "result": "Intermediate"}', today=TODAY)
    assert len(df) == 1 and dropped == 0
    assert df.loc[0, "city"] == "Unknown" and df.loc[0, "date"] == TODAY


def test_parse_llm_records_rejects_non_json():
    with pytest.raises(json.JSONDecodeError):
        u.parse_llm_records("Sorry, I cannot help with that.")


def test_parse_llm_records_rejects_scalar_json():
    with pytest.raises(ValueError):
        u.parse_llm_records("42")


# ── statistics ───────────────────────────────────────────────────────────────
def test_resistance_rate():
    s = pd.Series(["Resistant", "Susceptible", "Resistant", "Intermediate"])
    assert u.resistance_rate(s) == 50.0
    assert u.resistance_rate(pd.Series(["Resistant"] * 2 + ["Susceptible"])) == 66.7
    assert u.resistance_rate(pd.Series([], dtype=object)) == 0.0


def test_rate_table_sorted_with_counts():
    df = pd.DataFrame({
        "antibiotic": ["A", "A", "B", "B", "B", "B"],
        "result": ["Resistant", "Resistant", "Resistant", "Susceptible", "Susceptible", "Susceptible"],
    })
    t = u.rate_table(df, "antibiotic")
    assert t.index.tolist() == ["A", "B"]
    assert t["rate"].tolist() == [100.0, 25.0]
    assert t["n"].tolist() == [2, 4]


# ── demo data ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def glass():
    return pd.read_csv(os.path.join(ROOT, "data", "glass_rates_pakistan_2023.csv"))


def test_glass_table_is_valid(glass):
    assert not glass.duplicated(["organism", "antibiotic"]).any()
    assert glass["percent_resistant"].between(0, 100).all()
    assert (glass["n_resistant"] <= glass["n_tested"]).all()


def test_generate_demo_data_reproduces_committed_csv(glass):
    """amr_data.csv must be exactly what the documented pipeline produces."""
    generated = u.generate_demo_data(glass, n_rows=300, seed=42)
    committed = pd.read_csv(os.path.join(ROOT, "amr_data.csv"))
    pd.testing.assert_frame_equal(generated, committed)


def test_generate_demo_data_shape_and_values(glass):
    df = u.generate_demo_data(glass, n_rows=50, seed=1)
    assert len(df) == 50 and list(df.columns) == u.RESULT_COLS
    assert set(df["result"]) <= set(u.RESULTS)
    assert set(df["city"]) <= set(u.DEMO_CITIES)
    pairs = set(zip(glass["organism"], glass["antibiotic"]))
    assert set(zip(df["organism"], df["antibiotic"])) <= pairs


def test_zero_percent_pairs_are_never_resistant(glass):
    df = u.generate_demo_data(glass, n_rows=2000, seed=7)
    zero = glass[glass["percent_resistant"] == 0]
    merged = df.merge(zero, on=["organism", "antibiotic"])
    assert len(merged) > 0 and (merged["result"] != "Resistant").all()
