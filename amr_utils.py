"""
AMR Guardian — pure data helpers shared by app.py, the notebook and the tests.
Nothing in this module depends on Streamlit or on an API key.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

RESULT_COLS = ["city", "organism", "antibiotic", "result", "date"]
RESULTS     = ["Resistant", "Susceptible", "Intermediate"]

RESULT_MAP = {
    "R": "Resistant", "RESISTANT": "Resistant", "RES": "Resistant",
    "S": "Susceptible", "SUSCEPTIBLE": "Susceptible", "SENSITIVE": "Susceptible",
    "SUS": "Susceptible",
    "I": "Intermediate", "INTERMEDIATE": "Intermediate", "INT": "Intermediate",
    "SDD": "Intermediate",
}

COLUMN_ALIASES = {
    "organism":   ["pathogen", "bacteria", "bug", "microorganism", "organism_name", "species"],
    "antibiotic": ["drug", "antimicrobial", "agent", "antibiotic_name", "abx", "medication",
                   "antimicrobial_agent"],
    "result":     ["susceptibility", "interpretation", "sir", "outcome", "mic_interp", "category",
                   "susceptibility_category"],
    "city":       ["location", "hospital_city", "site", "region", "hospital", "centre", "center",
                   "facility_city", "facility"],
    "date":       ["test_date", "report_date", "collection_date", "sample_date", "datetime",
                   "timestamp", "dt", "collection_dt"],
}

DEMO_CITIES = ["Karachi", "Lahore", "Islamabad", "Peshawar",
               "Quetta", "Rawalpindi", "Faisalabad", "Multan"]


# ── Cleaning ──────────────────────────────────────────────────────────────────
def normalize_result(series: pd.Series) -> pd.Series:
    """Map S/I/R codes and spelling variants to Resistant/Susceptible/Intermediate.
    Values that cannot be mapped become NaN."""
    return series.astype(str).str.strip().str.upper().map(RESULT_MAP)


def clean_records(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Keep the 5 core columns, strip text, parse dates, normalise results.
    Rows whose result cannot be mapped are dropped. Returns (clean_df, n_dropped)."""
    df = df[RESULT_COLS].copy()
    for c in ["city", "organism", "antibiotic"]:
        df[c] = df[c].astype(str).str.strip()
    df["date"]   = pd.to_datetime(df["date"], errors="coerce")
    df["result"] = normalize_result(df["result"])
    before = len(df)
    df = df.dropna(subset=["result"]).reset_index(drop=True)
    return df, before - len(df)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case/strip column names, drop pandas index columns and rename known aliases
    (e.g. pathogen → organism). Returns a new DataFrame; missing columns are left missing."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.replace("﻿", "", regex=False).str.strip().str.lower()
    df = df.loc[:, ~df.columns.str.startswith("unnamed")]
    cols = set(df.columns)
    rename_map = {}
    for standard, aliases in COLUMN_ALIASES.items():
        if standard not in cols:
            match = next((a for a in aliases if a in cols), None)
            if match:
                rename_map[match] = standard
    return df.rename(columns=rename_map)


def missing_columns(df: pd.DataFrame) -> list[str]:
    return sorted(set(RESULT_COLS) - set(df.columns))


def parse_llm_records(text: str, today: pd.Timestamp | None = None) -> tuple[pd.DataFrame, int]:
    """Turn the LLM's JSON answer (an array of objects, or a single object) into clean
    isolate rows. Missing names become 'Unknown'; a missing/invalid date becomes `today`.
    Raises json.JSONDecodeError if the text is not JSON."""
    today = (today or pd.Timestamp.today()).normalize()
    text = text.strip().replace("```json", "").replace("```", "").strip()
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON array of results.")
    records = [{k: p.get(k) for k in RESULT_COLS} for p in parsed if isinstance(p, dict)]
    df = pd.DataFrame(records, columns=RESULT_COLS)
    df[["organism", "antibiotic", "city"]] = df[["organism", "antibiotic", "city"]].fillna("Unknown")
    df, n_dropped = clean_records(df)
    df["date"] = df["date"].fillna(today)
    return df, n_dropped


# ── Statistics ────────────────────────────────────────────────────────────────
def resistance_rate(results: pd.Series) -> float:
    """% of results that are Resistant, rounded to 1 decimal (0.0 for an empty series)."""
    if len(results) == 0:
        return 0.0
    return round(float((results == "Resistant").mean()) * 100, 1)


def rate_table(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    """Resistance rate and isolate count per group, highest rate first.
    Columns: rate (%), n (isolates)."""
    g = df.groupby(by)["result"]
    return (pd.DataFrame({"rate": g.apply(resistance_rate), "n": g.size()})
              .sort_values("rate", ascending=False))


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k resistant out of n, in percent."""
    if n == 0:
        return (0.0, 100.0)
    p = k / n
    denom  = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half   = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (round(100 * max(0.0, centre - half), 1), round(100 * min(1.0, centre + half), 1))


def compare_with_reference(df: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Per organism–antibiotic pair: observed resistance in `df` vs. the reference rate
    (e.g. WHO GLASS), with n, 95% Wilson CI and whether the reference lies inside it."""
    obs = (df.groupby(["organism", "antibiotic"])["result"]
             .agg(n="size", k=lambda s: int((s == "Resistant").sum()))
             .reset_index())
    out = obs.merge(reference[["organism", "antibiotic", "percent_resistant"]],
                    on=["organism", "antibiotic"], how="inner")
    out["observed_rate"]  = (100 * out["k"] / out["n"]).round(1)
    out["reference_rate"] = out["percent_resistant"].round(1)
    cis = [wilson_interval(k, n) for k, n in zip(out["k"], out["n"])]
    out["ci_low"]  = [c[0] for c in cis]
    out["ci_high"] = [c[1] for c in cis]
    out["reference_inside_ci"] = out["reference_rate"].between(out["ci_low"], out["ci_high"])
    out["abs_diff"] = (out["observed_rate"] - out["reference_rate"]).abs().round(1)
    return (out.drop(columns=["percent_resistant", "k"])
               .sort_values("abs_diff", ascending=False)
               .reset_index(drop=True))


# ── Demo-data generation (used by the notebook and the DVC pipeline) ──────────
def generate_demo_data(glass_df: pd.DataFrame, n_rows: int = 300,
                       cities: list[str] = DEMO_CITIES, seed: int = 42,
                       intermediate_share: float = 0.10) -> pd.DataFrame:
    """Synthetic isolate rows: each row picks a random organism–antibiotic pair from the
    WHO GLASS table and draws its result from that pair's national resistance rate.
    City and date are random — so only organism/antibiotic-level rates are meaningful."""
    np.random.seed(seed)
    random.seed(seed)
    lookup = {(r.organism, r.antibiotic): r.percent_resistant / 100.0
              for r in glass_df.itertuples()}
    pairs = list(lookup.keys())
    start = datetime(2023, 1, 1)
    records = []
    for _ in range(n_rows):
        organism, antibiotic = random.choice(pairs)
        prob_r = lookup[(organism, antibiotic)]
        u = np.random.random()
        if u < prob_r:
            result = "Resistant"
        elif u < prob_r + intermediate_share:
            result = "Intermediate"
        else:
            result = "Susceptible"
        records.append({
            "city":       random.choice(cities),
            "organism":   organism,
            "antibiotic": antibiotic,
            "result":     result,
            "date":       (start + timedelta(days=random.randint(0, 364))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(records, columns=RESULT_COLS)
