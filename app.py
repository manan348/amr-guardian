"""
AMR Guardian — Streamlit Dashboard
Deploy on Streamlit Community Cloud.
"""

import os
import io
import json
import html
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from groq import Groq

from amr_utils import (
    RESULT_COLS, clean_records, standardize_columns, missing_columns,
    parse_llm_records, resistance_rate, rate_table,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMR Guardian",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0e1a;
    --surface:   #111827;
    --border:    #1e2d40;
    --accent:    #00d4aa;
    --accent2:   #ff6b6b;
    --accent3:   #ffd166;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --resistant: #ff6b6b;
    --susceptible:#00d4aa;
    --intermediate:#ffd166;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    background-color: var(--bg);
    color: var(--text);
}

.amr-header {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 24px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
    background: linear-gradient(90deg, rgba(0,212,170,0.04) 0%, transparent 60%);
    border-radius: 0 0 0 0;
}
.amr-title {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -1px;
    margin: 0;
}
.amr-subtitle {
    font-size: 0.87rem;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    margin: 0;
}

.kpi-row { display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }
.kpi-card {
    flex: 1;
    min-width: 160px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
}
.kpi-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}
.kpi-value.red   { color: var(--resistant); }
.kpi-value.green { color: var(--susceptible); }
.kpi-value.yellow{ color: var(--intermediate); }
.kpi-value.white { color: var(--text); }

.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    padding-left: 2px;
}

.chat-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    height: 360px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 12px;
}
.msg { display: flex; gap: 10px; align-items: flex-start; }
.msg.user  { flex-direction: row-reverse; }
.msg-bubble {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.55;
    white-space: pre-wrap;
}
.msg.assistant .msg-bubble {
    background: #1a2744;
    border: 1px solid var(--border);
    color: var(--text);
    border-top-left-radius: 4px;
}
.msg.user .msg-bubble {
    background: #004d3d;
    color: var(--text);
    border: 1px solid #006655;
    border-top-right-radius: 4px;
}
.avatar {
    width: 32px; height: 32px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
}
.avatar.bot { background: #002a20; color: var(--accent); border: 1px solid #006655; }
.avatar.user-av { background: #1a2744; color: #7aa4f0; border: 1px solid var(--border); }

.bulletin-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 28px 32px;
    font-size: 0.92rem;
    line-height: 1.7;
    white-space: pre-wrap;
    color: var(--text);
}
.alert-box {
    background: #2d0a0a;
    border: 1px solid #7a2020;
    border-left: 4px solid var(--resistant);
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
    font-size: 0.9rem;
    color: #ffb3b3;
}
.upload-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 24px;
}
.parsed-card {
    background: #0d2e26;
    border: 1px solid #006655;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 16px;
    font-size: 0.9rem;
}
.parsed-row {
    display: flex;
    gap: 12px;
    padding: 6px 0;
    border-bottom: 1px solid #1e4030;
    font-size: 0.88rem;
}
.parsed-key {
    font-family: 'Space Mono', monospace;
    color: var(--accent);
    min-width: 120px;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.parsed-val { color: var(--text); }

div[data-testid="stPlotlyChart"] { background: transparent !important; }
.stTextArea textarea {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
}
.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.77rem !important;
    letter-spacing: 1px !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
DATA_PATH = "amr_data.csv"
PLOT_CFG  = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
    font=dict(color="#e2e8f0"),
)
COLORS = {"Resistant": "#ff6b6b", "Susceptible": "#00d4aa", "Intermediate": "#ffd166"}

CITY_COORDS = {
    "Karachi":   {"lat": 24.8607, "lon": 67.0011},
    "Lahore":    {"lat": 31.5497, "lon": 74.3436},
    "Islamabad": {"lat": 33.6844, "lon": 73.0479},
    "Peshawar":  {"lat": 34.0151, "lon": 71.5249},
    "Quetta":    {"lat": 30.1798, "lon": 66.9750},
    "Rawalpindi":{"lat": 33.5651, "lon": 73.0169},
    "Faisalabad":{"lat": 31.4504, "lon": 73.1350},
    "Multan":    {"lat": 30.1575, "lon": 71.5249},
}

GROQ_MODEL        = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_AI_CALLS      = 20   # per browser session — protects the shared API quota
CHAT_HISTORY_SENT = 10   # only the last N chat messages are sent to the model
MIN_ISOLATES      = 30   # CLSI M39: rates from fewer isolates are unreliable

def esc(value) -> str:
    """HTML-escape any user- or LLM-provided value before it goes into raw HTML."""
    return html.escape(str(value))

def ai_quota_ok() -> bool:
    """Per-session limit on Groq calls. Shows an error and returns False when exhausted."""
    used = st.session_state.get("ai_calls", 0)
    if used >= MAX_AI_CALLS:
        st.error(f"AI request limit reached for this session ({MAX_AI_CALLS}). "
                 "Reload the page to start a new session.")
        return False
    st.session_state.ai_calls = used + 1
    return True

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df, _ = clean_records(standardize_columns(pd.read_csv(path)))
    return df

def get_groq_client():
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None
    return Groq(api_key=api_key)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = load_data(DATA_PATH)
    data_ok = True
except FileNotFoundError:
    st.warning(f"Data file not found at `{DATA_PATH}`. Using demo data.")
    import numpy as np
    np.random.seed(42)
    orgs   = ["Escherichia coli","Klebsiella pneumoniae","Acinetobacter spp.",
               "Salmonella spp.","Streptococcus pneumoniae"]
    abx    = ["Ceftriaxone","Meropenem","Co-trimoxazole","Ampicillin","Ciprofloxacin"]
    cities = list(CITY_COORDS.keys())
    n = 300
    df = pd.DataFrame({
        "city":       np.random.choice(cities, n),
        "organism":   np.random.choice(orgs, n),
        "antibiotic": np.random.choice(abx, n),
        "result":     np.random.choice(["Resistant","Susceptible","Intermediate"],
                                       n, p=[0.47, 0.42, 0.11]),
        "date":       pd.date_range("2023-01-01", periods=n, freq="D")[:n],
    })
    data_ok = False

# Session state: working dataset (can be extended by uploads)
if "working_df" not in st.session_state:
    st.session_state.working_df = df.copy()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;padding:8px 0 12px">
  <svg width="36" height="36" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="32" cy="32" r="30" stroke="#00d4aa" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.4"/>
    <circle cx="32" cy="32" r="22" fill="#0d2e26" stroke="#00d4aa" stroke-width="1.5"/>
    <path d="M24 18 C24 22 28 24 28 28 C28 32 24 34 24 38 C24 42 28 44 28 46"
          stroke="#00d4aa" stroke-width="2" stroke-linecap="round" fill="none"/>
    <path d="M40 18 C40 22 36 24 36 28 C36 32 40 34 40 38 C40 42 36 44 36 46"
          stroke="#ffd166" stroke-width="2" stroke-linecap="round" fill="none"/>
    <line x1="24" y1="22" x2="40" y2="22" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
    <line x1="28" y1="28" x2="36" y2="28" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
    <line x1="24" y1="34" x2="40" y2="34" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
    <line x1="28" y1="40" x2="36" y2="40" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
    <circle cx="32" cy="32" r="2.5" fill="#00d4aa"/>
  </svg>
  <div>
    <div style="font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;
                color:#00d4aa;letter-spacing:-0.5px;line-height:1">AMR Guardian</div>
    <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#64748b;
                margin-top:3px;letter-spacing:0.5px">Pakistan · WHO GLASS 2023</div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("---")

    wdf = st.session_state.working_df
    organisms   = ["All"] + sorted(wdf["organism"].unique().tolist())
    antibiotics = ["All"] + sorted(wdf["antibiotic"].unique().tolist())
    cities_list = ["All"] + sorted(wdf["city"].unique().tolist())

    sel_org  = st.selectbox("Organism",   organisms)
    sel_abx  = st.selectbox("Antibiotic", antibiotics)
    sel_city = st.selectbox("City",       cities_list)

    st.markdown("---")
    st.markdown('<p class="section-title">WHO Reference Rates (PK 2023)</p>',
                unsafe_allow_html=True)
    ref_data = [
        ("Klebsiella + Ceftriaxone",  84),
        ("Strep + Co-trimoxazole",    87),
        ("E. coli + Ceftriaxone",     83),
        ("Acinetobacter + Meropenem", 68),
        ("Klebsiella + Meropenem",    59),
        ("Salmonella + Ceftriaxone",  49),
    ]
    for label, rate in ref_data:
        color = "#ff6b6b" if rate >= 70 else "#ffd166" if rate >= 50 else "#00d4aa"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.77rem;padding:4px 0;border-bottom:1px solid #1e2d40">'
            f'<span style="color:#94a3b8">{label}</span>'
            f'<span style="font-family:Space Mono,monospace;font-weight:700;color:{color}">'
            f'{rate}%</span></div>',
            unsafe_allow_html=True,
        )

# ── Filter ────────────────────────────────────────────────────────────────────
fdf = st.session_state.working_df.copy()
if sel_org  != "All": fdf = fdf[fdf["organism"]   == sel_org]
if sel_abx  != "All": fdf = fdf[fdf["antibiotic"] == sel_abx]
if sel_city != "All": fdf = fdf[fdf["city"]        == sel_city]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="amr-header">

  <!-- SVG Wordmark Logo -->
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Outer ring -->
    <circle cx="32" cy="32" r="30" stroke="#00d4aa" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.4"/>
    <!-- Inner circle -->
    <circle cx="32" cy="32" r="22" fill="#0d2e26" stroke="#00d4aa" stroke-width="1.5"/>
    <!-- DNA helix left strand -->
    <path d="M24 18 C24 22 28 24 28 28 C28 32 24 34 24 38 C24 42 28 44 28 46"
          stroke="#00d4aa" stroke-width="2" stroke-linecap="round" fill="none"/>
    <!-- DNA helix right strand -->
    <path d="M40 18 C40 22 36 24 36 28 C36 32 40 34 40 38 C40 42 36 44 36 46"
          stroke="#ffd166" stroke-width="2" stroke-linecap="round" fill="none"/>
    <!-- Cross-links -->
    <line x1="24" y1="22" x2="40" y2="22" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
    <line x1="28" y1="28" x2="36" y2="28" stroke="#00d4aa" stroke-width="1.2" opacity="0.7"/>
    <line x1="24" y1="34" x2="40" y2="34" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
    <line x1="28" y1="40" x2="36" y2="40" stroke="#ffd166" stroke-width="1.2" opacity="0.7"/>
    <!-- Shield overlay bottom -->
    <path d="M26 44 Q32 48 38 44" stroke="#00d4aa" stroke-width="1.5" fill="none" stroke-linecap="round"/>
    <!-- Pulse dot -->
    <circle cx="32" cy="32" r="2.5" fill="#00d4aa"/>
    <circle cx="32" cy="32" r="2.5" fill="#00d4aa" opacity="0.3">
      <animate attributeName="r" values="2.5;6;2.5" dur="2.5s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.3;0;0.3" dur="2.5s" repeatCount="indefinite"/>
    </circle>
  </svg>

  <div style="flex:1">
    <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
      <p class="amr-title" style="margin:0">AMR Guardian</p>
      <span style="font-family:'Space Mono',monospace;font-size:0.65rem;letter-spacing:2px;
                   color:#00d4aa;background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.3);
                   padding:3px 10px;border-radius:20px;">DEMO DATA</span>
    </div>
    <p class="amr-subtitle" style="margin:6px 0 0">
      Antimicrobial Resistance Surveillance &nbsp;·&nbsp; Pakistan &nbsp;·&nbsp; WHO GLASS 2023
    </p>
  </div>

  <!-- Right side stats pill -->
  <div style="text-align:right;font-family:'Space Mono',monospace;font-size:0.7rem;
              color:#64748b;line-height:1.8;display:none" class="header-meta">
  </div>

</div>
""", unsafe_allow_html=True)

st.info(
    "**Demo dataset.** The bundled `amr_data.csv` is synthetic: each organism–antibiotic "
    "result is sampled from national WHO GLASS Pakistan 2023 resistance rates, but cities and "
    "dates are assigned at random. City, map and trend patterns are illustrative only. "
    "Upload your own lab data for real surveillance."
)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — File Upload Tab for Lab Reports
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("Upload Lab Report — Auto-parse & Add to Dataset", expanded=False):
    st.markdown('<p class="section-title">Lab Report Parser</p>', unsafe_allow_html=True)

    upload_col1, upload_col2 = st.columns([3, 2])
    with upload_col1:
        uploaded_file = st.file_uploader(
            "Upload .txt lab report or .csv data file",
            type=["txt", "csv"],
            key="lab_upload",
        )
        report_text_area = st.text_area(
            "Or paste raw lab report text",
            placeholder="e.g.\nOrganism: Klebsiella pneumoniae\nCeftriaxone: R (MIC >32)\nMeropenem: S\nCity: Lahore\nDate: 2024-03-15",
            height=140,
            key="lab_text_input",
        )

    with upload_col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        parse_btn = st.button("PARSE REPORT", key="parse_report_btn", use_container_width=True)
        st.caption("CSV files need the columns `city, organism, antibiotic, result, date` "
                   "(result may be S/I/R or full words).")

    # Everything below runs only on click — st.file_uploader keeps its file across
    # reruns, so doing this unconditionally would re-merge the same CSV every rerun.
    if parse_btn:
        is_csv = uploaded_file is not None and uploaded_file.name.lower().endswith(".csv")
        raw_report = ""
        if uploaded_file is not None and not is_csv:
            try:
                raw_report = uploaded_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error("Could not read file. Please upload a valid UTF-8 .txt file.")
        elif uploaded_file is None:
            raw_report = report_text_area.strip()

        if is_csv:
            fingerprint = (uploaded_file.name, uploaded_file.size)
            if fingerprint in st.session_state.get("merged_uploads", set()):
                st.info(f"`{uploaded_file.name}` has already been added to the dataset in this session.")
            else:
                try:
                    csv_df = standardize_columns(
                        pd.read_csv(io.BytesIO(uploaded_file.getvalue()), encoding="utf-8-sig")
                    )
                    missing = missing_columns(csv_df)
                    if missing:
                        st.error(
                            f"**Unrecognised CSV format.** Missing column(s): `{', '.join(missing)}`.\n\n"
                            f"Columns found: `{', '.join(sorted(csv_df.columns))}`\n\n"
                            f"Required: `city, organism, antibiotic, result, date` (one row per isolate test)."
                        )
                    else:
                        csv_df, n_dropped = clean_records(csv_df)
                        if csv_df.empty:
                            st.error("No usable rows: the `result` column must contain S/I/R or "
                                     "Resistant/Susceptible/Intermediate.")
                        else:
                            st.session_state.working_df = pd.concat(
                                [st.session_state.working_df, csv_df], ignore_index=True
                            )
                            st.session_state.setdefault("merged_uploads", set()).add(fingerprint)
                            st.success(f"CSV merged — {len(csv_df)} isolate rows added to the dataset.")
                            if n_dropped:
                                st.warning(f"{n_dropped} row(s) skipped because their result was not S/I/R.")
                except Exception as e:
                    st.error(f"Could not read CSV: {e}")

        elif not raw_report:
            st.warning("Please paste a lab report or upload a .txt or .csv file first.")
        else:
            client = get_groq_client()
            if client is None:
                st.error("GROQ_API_KEY not found.")
            elif ai_quota_ok():
                today = pd.Timestamp.today().normalize()
                with st.spinner("Parsing lab report with Groq…"):
                    try:
                        parse_prompt = f"""You are a clinical microbiology data extractor.
Extract every antibiotic susceptibility result from this lab report and return ONLY a valid JSON array — no markdown, no backticks, no explanation.

Each element must be an object:
{{
  "organism": "full organism name",
  "antibiotic": "antibiotic name",
  "result": "Resistant" or "Susceptible" or "Intermediate",
  "city": "city name in Pakistan, or Unknown",
  "date": "YYYY-MM-DD, or null if not stated"
}}

Return one element per antibiotic tested. Do not invent results that are not in the report.

LAB REPORT:
{raw_report}"""

                        parse_response = client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=[{"role": "user", "content": parse_prompt}],
                            temperature=0.1,
                            max_tokens=800,
                        )
                        new_df, n_dropped = parse_llm_records(
                            parse_response.choices[0].message.content, today=today
                        )

                        if new_df.empty:
                            st.error("Parsing returned no valid results. Please check the report format.")
                        else:
                            rows_html = "".join(
                                f'<div class="parsed-row">'
                                f'<span class="parsed-key">{esc(r.antibiotic)}</span>'
                                f'<span class="parsed-val" style="color:{COLORS[r.result]}">{esc(r.result)}</span>'
                                f'<span class="parsed-val" style="color:#94a3b8">'
                                f'{esc(r.organism)} · {esc(r.city)} · {r.date:%Y-%m-%d}</span></div>'
                                for r in new_df.itertuples()
                            )
                            st.markdown(f"""
<div class="parsed-card">
  <div style="font-family:'Space Mono',monospace;color:var(--accent);font-size:0.78rem;
              letter-spacing:1px;margin-bottom:12px;">PARSED {len(new_df)} RESULT(S)</div>
  {rows_html}
</div>
""", unsafe_allow_html=True)
                            st.session_state.working_df = pd.concat(
                                [st.session_state.working_df, new_df], ignore_index=True
                            )
                            st.success(f"{len(new_df)} record(s) added to the dataset — "
                                       "charts will update on the next interaction.")
                            if n_dropped:
                                st.warning(f"{n_dropped} extracted result(s) skipped (result not S/I/R).")
                    except json.JSONDecodeError:
                        st.error("Could not parse JSON from Groq response. Try rephrasing the report.")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ── KPI cards ─────────────────────────────────────────────────────────────────
total   = len(fdf)
n_res   = (fdf["result"] == "Resistant").sum()
n_sus   = (fdf["result"] == "Susceptible").sum()
n_int   = (fdf["result"] == "Intermediate").sum()
res_pct = round(n_res / total * 100, 1) if total else 0

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Total Isolates</div>
    <div class="kpi-value white">{total:,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Resistant</div>
    <div class="kpi-value red">{n_res}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Susceptible</div>
    <div class="kpi-value green">{n_sus}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Intermediate</div>
    <div class="kpi-value yellow">{n_int}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Resistance Rate</div>
    <div class="kpi-value {'red' if res_pct > 60 else 'yellow' if res_pct > 40 else 'green'}">{res_pct}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Charts: row 1 ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown('<p class="section-title">Resistance Rate by Organism</p>',
                unsafe_allow_html=True)
    if fdf.empty:
        st.info("No data matches the current filters — adjust the sidebar selections to see this chart.")
    else:
        org_stats = (
            fdf.groupby("organism")["result"]
            .apply(resistance_rate)
            .reset_index(name="resistance_rate")
            .sort_values("resistance_rate", ascending=True)
        )
        colors_bar = [
            "#ff6b6b" if v >= 70 else "#ffd166" if v >= 40 else "#00d4aa"
            for v in org_stats["resistance_rate"]
        ]
        fig_bar = go.Figure(go.Bar(
            x=org_stats["resistance_rate"],
            y=org_stats["organism"],
            orientation="h",
            marker_color=colors_bar,
            marker_line_width=0,
        ))
        fig_bar.update_layout(
            **PLOT_CFG,
            xaxis=dict(gridcolor="#1e2d40", ticksuffix="%", range=[0, 100]),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown('<p class="section-title">Resistance Trend Over Time</p>',
                unsafe_allow_html=True)
    if fdf.empty:
        st.info("No data matches the current filters — adjust the sidebar selections to see the trend chart.")
    else:
        trend = (
            fdf.set_index("date")["result"]
            .resample("2W")
            .apply(lambda s: resistance_rate(s) if len(s) else None)
            .dropna()
            .reset_index(name="resistance_rate")
        )
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=trend["date"], y=trend["resistance_rate"],
            mode="lines+markers",
            line=dict(color="#00d4aa", width=2.5, shape="spline"),
            marker=dict(size=6, color="#00d4aa", line=dict(width=1.5, color="#0a0e1a")),
            fill="tozeroy",
            fillcolor="rgba(0,212,170,0.08)",
            name="Resistance %",
        ))
        fig_line.update_layout(
            **PLOT_CFG,
            xaxis=dict(gridcolor="#1e2d40"),
            yaxis=dict(gridcolor="#1e2d40", ticksuffix="%", range=[0, 100]),
            showlegend=False,
            height=320,
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ── Charts: row 2 ─────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown('<p class="section-title">City-wise Resistance Breakdown</p>',
                unsafe_allow_html=True)
    fig_city = go.Figure()
    cities_sorted = sorted(fdf["city"].unique())
    for result_type, color in COLORS.items():
        counts = [
            len(fdf[(fdf["city"] == c) & (fdf["result"] == result_type)])
            for c in cities_sorted
        ]
        fig_city.add_trace(go.Bar(
            name=result_type, x=cities_sorted, y=counts,
            marker_color=color,
        ))
    fig_city.update_layout(
        **PLOT_CFG,
        barmode="stack",
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="#1e2d40", title="Isolates"),
        legend=dict(orientation="h", y=1.08, x=0),
        height=320,
    )
    st.plotly_chart(fig_city, use_container_width=True)

with col4:
    st.markdown('<p class="section-title">Resistance Heatmap (Organism × City)</p>',
                unsafe_allow_html=True)
    if fdf.empty:
        st.info("No data matches the current filters — adjust the sidebar selections to see the heatmap.")
    else:
        grp  = fdf.groupby(["organism", "city"])["result"]
        # Cells with no isolates stay empty (NaN) instead of showing a misleading 0%
        heat = grp.apply(resistance_rate).unstack()
        heat_n = grp.size().unstack().reindex_like(heat).fillna(0).astype(int)
        heat.index = (heat.index
            .str.replace("Escherichia coli",        "E. coli")
            .str.replace("Klebsiella pneumoniae",    "K. pneumoniae")
            .str.replace("Streptococcus pneumoniae", "S. pneumoniae")
        )
        cell_text = [
            [("" if pd.isna(v) else f"{v}%" + ("*" if n < MIN_ISOLATES else ""))
             for v, n in zip(row_v, row_n)]
            for row_v, row_n in zip(heat.values, heat_n.values)
        ]
        fig_heat = go.Figure(go.Heatmap(
            z=heat.values,
            x=heat.columns.tolist(),
            y=heat.index.tolist(),
            colorscale=[[0, "#0d2e26"], [0.5, "#ffd166"], [1, "#ff6b6b"]],
            zmin=0, zmax=100,
            text=cell_text,
            customdata=heat_n.values,
            hovertemplate="%{y} · %{x}<br>Resistance: %{z}%<br>Isolates: %{customdata}<extra></extra>",
            texttemplate="%{text}",
            textfont=dict(family="Space Mono", size=11),
            colorbar=dict(ticksuffix="%", tickfont=dict(family="Space Mono", size=10)),
        ))
        fig_heat.update_layout(
            **PLOT_CFG,
            xaxis=dict(side="bottom"),
            height=320,
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ── Antibiotic breakdown table ─────────────────────────────────────────────────
st.markdown('<p class="section-title">Antibiotic Resistance Summary</p>',
            unsafe_allow_html=True)
if fdf.empty:
    st.info("No data matches the current filters — adjust the sidebar selections to see the antibiotic table.")
else:
    abx_summary = (
        fdf.groupby("antibiotic")["result"]
        .value_counts(normalize=True)
        .mul(100).round(1)
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["Resistant", "Susceptible", "Intermediate"]:
        if col not in abx_summary.columns:
            abx_summary[col] = 0.0
    abx_summary = abx_summary.rename(columns={"antibiotic": "Antibiotic"})
    abx_summary["Total Isolates"] = abx_summary["Antibiotic"].map(fdf.groupby("antibiotic").size())
    abx_summary["Note"] = abx_summary["Total Isolates"].map(
        lambda n: f"Low confidence (n<{MIN_ISOLATES})" if n < MIN_ISOLATES else ""
    )
    abx_summary = abx_summary.sort_values("Resistant", ascending=False)

    # High resistance is bad (red); high susceptibility is good (green).
    def color_resistant(val):
        if val >= 70:   return "color: #ff6b6b; font-weight: 600"
        elif val >= 50: return "color: #ffd166"
        return "color: #00d4aa"

    def color_susceptible(val):
        if val >= 70:   return "color: #00d4aa; font-weight: 600"
        elif val >= 50: return "color: #ffd166"
        return "color: #ff6b6b"

    styled = (
        abx_summary[["Antibiotic", "Resistant", "Susceptible", "Intermediate", "Total Isolates", "Note"]]
        .style
        .set_properties(**{
            "background-color": "#111827",
            "color":            "#e2e8f0",
            "border-color":     "#1e2d40",
            "font-family":      "DM Sans, sans-serif",
            "font-size":        "0.9rem",
        })
        .map(color_resistant,   subset=["Resistant"])
        .map(color_susceptible, subset=["Susceptible"])
        .format({"Resistant": "{:.1f}%", "Susceptible": "{:.1f}%", "Intermediate": "{:.1f}%"})
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#0a0e1a"),
                ("color",            "#64748b"),
                ("font-family",      "Space Mono, monospace"),
                ("font-size",        "0.72rem"),
                ("letter-spacing",   "1px"),
                ("text-transform",   "uppercase"),
                ("border-bottom",    "1px solid #1e2d40"),
            ]},
            {"selector": "tr:hover td", "props": [("background-color", "#1a2744")]},
        ])
    )
    st.dataframe(styled, use_container_width=True, height=220)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — Pakistan City Choropleth / Bubble Map
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-title">Resistance Intensity Map — Pakistan Cities</p>',
            unsafe_allow_html=True)

map_df = (
    st.session_state.working_df.groupby("city")["result"]
    .apply(resistance_rate)
    .reset_index(name="resistance_rate")
)
map_df["lat"] = map_df["city"].map(lambda c: CITY_COORDS.get(c, {}).get("lat"))
map_df["lon"] = map_df["city"].map(lambda c: CITY_COORDS.get(c, {}).get("lon"))
map_df["isolates"] = map_df["city"].map(
    st.session_state.working_df.groupby("city").size()
)
map_df = map_df.dropna(subset=["lat", "lon"])

if not map_df.empty:
    fig_map = go.Figure()
    fig_map.add_trace(go.Scattergeo(
        lat=map_df["lat"],
        lon=map_df["lon"],
        text=map_df.apply(
            lambda r: f"{r['city']}<br>Resistance: {r['resistance_rate']}%<br>Isolates: {int(r['isolates'])}",
            axis=1,
        ),
        mode="markers+text",
        textposition="top center",
        textfont=dict(family="Space Mono", size=11, color="#e2e8f0"),
        marker=dict(
            size=map_df["isolates"] / map_df["isolates"].max() * 40 + 18,
            color=map_df["resistance_rate"],
            colorscale=[[0, "#0d2e26"], [0.4, "#ffd166"], [1, "#ff6b6b"]],
            cmin=0, cmax=100,
            colorbar=dict(
                title=dict(text="Resistance %",
                           font=dict(family="Space Mono", size=10, color="#64748b")),
                ticksuffix="%",
                tickfont=dict(family="Space Mono", size=10, color="#e2e8f0"),
                bgcolor="rgba(17,24,39,0.8)",
                bordercolor="#1e2d40",
            ),
            line=dict(width=1.5, color="#0a0e1a"),
            opacity=0.88,
        ),
        hoverinfo="text",
    ))
    fig_map.update_layout(
        geo=dict(
            scope="asia",
            center=dict(lat=30.3753, lon=69.3451),
            projection_scale=5,
            showland=True,
            landcolor="#111827",
            showocean=True,
            oceancolor="#0a0e1a",
            showcountries=True,
            countrycolor="#1e2d40",
            showcoastlines=True,
            coastlinecolor="#1e2d40",
            bgcolor="rgba(0,0,0,0)",
            lataxis_range=[23, 38],
            lonaxis_range=[60, 78],
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(color="#e2e8f0"),
        height=420,
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Map requires city names matching: Karachi, Lahore, Islamabad, Peshawar, Quetta.")

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — AI Weekly Bulletin Generator
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<p class="section-title">AI AMR Bulletin Generator</p>',
            unsafe_allow_html=True)

BULLETIN_WINDOWS = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All data": None}

bulletin_col1, bulletin_col2, bulletin_col3 = st.columns([2, 1.3, 1])
with bulletin_col1:
    bulletin_city = st.selectbox(
        "Select City for Bulletin",
        sorted(st.session_state.working_df["city"].unique().tolist()),
        key="bulletin_city",
    )
with bulletin_col2:
    bulletin_window = st.selectbox(
        "Period (ending at latest sample)",
        list(BULLETIN_WINDOWS.keys()),
        index=1,
        key="bulletin_window",
    )
with bulletin_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    gen_bulletin = st.button("GENERATE BULLETIN", key="gen_bulletin_btn", use_container_width=True)

if gen_bulletin:
    client = get_groq_client()
    city_data = st.session_state.working_df[
        st.session_state.working_df["city"] == bulletin_city
    ].dropna(subset=["date"])
    days = BULLETIN_WINDOWS[bulletin_window]
    if days is not None and not city_data.empty:
        period_end   = city_data["date"].max()
        period_start = period_end - pd.Timedelta(days=days - 1)
        city_data    = city_data[city_data["date"] >= period_start]

    if client is None:
        st.error("GROQ_API_KEY not found. Add it to Streamlit → Secrets.")
    elif city_data.empty:
        st.warning(f"No dated isolates for {bulletin_city} in the selected period.")
    elif ai_quota_ok():
        period_label = (f"{city_data['date'].min():%d %b %Y} – {city_data['date'].max():%d %b %Y}")
        total_city    = len(city_data)
        res_rate_city = resistance_rate(city_data["result"])
        abx_rates = rate_table(city_data, "antibiotic")
        org_rates = rate_table(city_data, "organism")
        failing_abx   = abx_rates[abx_rates["rate"] >= 60]
        critical_orgs = org_rates[org_rates["rate"] >= 70]

        def fmt(tbl):
            if tbl.empty:
                return "  None"
            return "\n".join(
                f"  {k}: {r.rate}% (n={r.n}{', LOW SAMPLE' if r.n < MIN_ISOLATES else ''})"
                for k, r in tbl.iterrows()
            )

        bulletin_data = f"""
CITY: {bulletin_city}
PERIOD: {period_label}
TOTAL ISOLATES: {total_city}
OVERALL RESISTANCE RATE: {res_rate_city}%

ANTIBIOTIC RESISTANCE RATES:
{fmt(abx_rates)}

ORGANISM RESISTANCE RATES:
{fmt(org_rates)}

ANTIBIOTICS FAILING (>=60% resistance):
{fmt(failing_abx)}

CRITICAL ORGANISMS (>=70% resistance):
{fmt(critical_orgs)}
"""

        bulletin_prompt = f"""You are a senior clinical microbiologist generating a formal AMR surveillance bulletin for {bulletin_city}, Pakistan, covering {period_label}.

Using the surveillance data below, write a structured 1-page bulletin in Markdown with these EXACT sections:

1. EXECUTIVE SUMMARY (2-3 sentences overview of the resistance situation)
2. ANTIBIOTICS FAILING (list antibiotics >=60% resistance with clinical implication for each)
3. EMPIRIC TREATMENT CONSIDERATIONS (by infection type: UTI, pneumonia, sepsis, wound — suggest alternatives when primary agents are failing)
4. RESISTANCE ALERT (critical organisms requiring infection control attention)
5. RECOMMENDED ACTIONS (3-4 bullet points for the hospital pharmacy/ID team)

Use clear clinical language. Be direct and actionable. Reference WHO GLASS Pakistan 2023 benchmarks where relevant.
Rates marked LOW SAMPLE come from fewer than {MIN_ISOLATES} isolates: state that they are uncertain and do not base strong recommendations on them.
Use only the numbers given below; do not invent data.

SURVEILLANCE DATA FOR {bulletin_city.upper()}:
{bulletin_data}"""

        with st.spinner(f"Generating AMR bulletin for {bulletin_city}…"):
            try:
                bulletin_response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": bulletin_prompt}],
                    temperature=0.3,
                    max_tokens=1200,
                )
                bulletin_text = bulletin_response.choices[0].message.content

                st.markdown(f"""
<div style="font-family:'Space Mono',monospace;font-size:0.72rem;color:#64748b;
            letter-spacing:1px;margin-bottom:8px;">
  AMR BULLETIN · {esc(bulletin_city.upper())} · {esc(period_label.upper())} · {total_city} ISOLATES
</div>
""", unsafe_allow_html=True)
                st.warning("AI-generated decision support — not a prescription. Verify against local "
                           "antibiograms and consult the ID/pharmacy team before changing therapy.")
                with st.container(border=True):
                    # Plain st.markdown (no raw HTML) so the model's Markdown renders and
                    # any HTML in the response is not executed.
                    st.markdown(bulletin_text)

                if not critical_orgs.empty:
                    alert_html = "".join(
                        f"<b>{esc(org)}</b> — {r.rate}% resistance (n={r.n})<br>"
                        for org, r in critical_orgs.iterrows()
                    )
                    st.markdown(f"""
<div class="alert-box">
  <b>CRITICAL RESISTANCE ALERT — {esc(bulletin_city.upper())}</b><br><br>
  {alert_html}
  Immediate infection control review recommended for carbapenem-resistant and ESBL-producing organisms.
</div>
""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Groq API error: {e}")

# ── Groq Chatbot ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">Lab Report Interpreter — Powered by Groq</p>',
            unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant",
         "content": ("Hello, Doctor. I'm your AMR Guardian assistant.\n\n"
                     "Paste a lab report or ask me about resistance patterns — "
                     "I'll interpret results using WHO Pakistan 2023 resistance data. "
                     "For example: 'Patient has Klebsiella pneumoniae, Ceftriaxone MIC 32 μg/mL'")}
    ]

resist_summary = (
    st.session_state.working_df.groupby("organism")["result"]
    .apply(lambda s: f"{round((s=='Resistant').mean()*100,1)}% resistant")
    .to_dict()
)
system_prompt = f"""You are AMR Guardian, an expert clinical microbiology AI assistant for Pakistani hospitals.
You interpret lab reports and antimicrobial susceptibility test (AST) results, providing actionable clinical guidance.

CURRENT DATASET SUMMARY (demo data sampled from WHO GLASS Pakistan 2023 rates, plus any user uploads):
{chr(10).join(f'  • {k}: {v}' for k, v in resist_summary.items())}

KEY WHO PAKISTAN 2023 RESISTANCE RATES:
  • Klebsiella + Ceftriaxone: 84% resistant
  • Streptococcus + Co-trimoxazole: 87% resistant
  • E. coli + Ceftriaxone: 83% resistant
  • Acinetobacter + Meropenem: 68% resistant (CRITICAL — carbapenem resistance)
  • Klebsiella + Meropenem: 59% resistant
  • Salmonella + Ceftriaxone: 49% resistant

GUIDELINES:
1. Always interpret MIC values and S/I/R classifications
2. Highlight critical resistances (carbapenem-resistant Acinetobacter, ESBL, etc.)
3. Suggest empiric therapy alternatives when resistance is high
4. Reference WHO GLASS Pakistan data when relevant
5. Flag isolates needing infection control measures
6. Be concise but clinically precise — you are speaking to a doctor
7. Never prescribe — recommend consultation with ID/pharmacy team for final decisions"""

chat_html = '<div class="chat-wrap" id="chat-scroll">'
for msg in st.session_state.chat_history:
    role = msg["role"]
    avatar_svg = '''<svg width="18" height="18" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="32" cy="32" r="22" fill="#0d2e26" stroke="#00d4aa" stroke-width="2"/><path d="M24 18 C24 22 28 24 28 28 C28 32 24 34 24 38 C24 42 28 44 28 46" stroke="#00d4aa" stroke-width="2.5" stroke-linecap="round" fill="none"/><path d="M40 18 C40 22 36 24 36 28 C36 32 40 34 40 38 C40 42 36 44 36 46" stroke="#ffd166" stroke-width="2.5" stroke-linecap="round" fill="none"/><line x1="24" y1="28" x2="40" y2="28" stroke="#00d4aa" stroke-width="1.5" opacity="0.8"/><line x1="24" y1="36" x2="40" y2="36" stroke="#ffd166" stroke-width="1.5" opacity="0.8"/><circle cx="32" cy="32" r="2.5" fill="#00d4aa"/></svg>'''
    avatar   = avatar_svg if role == "assistant" else "Dr"
    av_class = "bot" if role == "assistant" else "user-av"
    side     = "assistant" if role == "assistant" else "user"
    content  = esc(msg["content"]).replace("\n", "<br>")
    chat_html += f"""
    <div class="msg {side}">
      <div class="avatar {av_class}">{avatar}</div>
      <div class="msg-bubble">{content}</div>
    </div>"""
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# A widget's value can only be reset before it is created in a run, so clearing the
# input after a successful send is done via a flag on the following rerun.
if st.session_state.pop("clear_chat_input", False):
    st.session_state.chat_input = ""

col_inp, col_btn = st.columns([5, 1])
with col_inp:
    user_input = st.text_area(
        "Lab report or question",
        placeholder="Paste lab report here, e.g.:\nOrganism: Klebsiella pneumoniae\nCeftriaxone: R (MIC >32)\nMeropenem: R (MIC >8)\nTigecycline: S",
        label_visibility="collapsed",
        height=90,
        key="chat_input",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    send = st.button("SEND", use_container_width=True)

if send:
    if not user_input.strip():
        st.warning("Please enter a lab report or question before sending.")
    else:
        client = get_groq_client()
        if client is None:
            st.error("GROQ_API_KEY not found. Add it to Streamlit → Advanced Settings → Secrets.")
        elif ai_quota_ok():
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
            with st.spinner(f"Analyzing with Groq {GROQ_MODEL}…"):
                try:
                    # Send only the most recent messages to stay within the context window.
                    recent = st.session_state.chat_history[-CHAT_HISTORY_SENT:]
                    messages_payload = [{"role": "system", "content": system_prompt}] + [
                        {"role": m["role"], "content": m["content"]} for m in recent
                    ]
                    response = client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages_payload,
                        temperature=0.3,
                        max_tokens=700,
                    )
                    reply = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.session_state.clear_chat_input = True
                    st.rerun()
                except Exception as e:
                    st.session_state.chat_history.pop()  # drop the unanswered question
                    st.error(f"Groq API error: {e}")

if st.button("Clear Chat", key="clear_chat"):
    st.session_state.chat_history = st.session_state.chat_history[:1]
    st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2d40;
            display:flex;justify-content:space-between;align-items:center">
  <span style="font-family:Space Mono,monospace;font-size:0.72rem;color:#334155">
    AMR Guardian · WHO GLASS Pakistan 2023 · Built with Streamlit + Groq
  </span>
  <span style="font-family:Space Mono,monospace;font-size:0.72rem;color:#334155">
    For clinical decision support only — not a substitute for ID consultation
  </span>
</div>
""", unsafe_allow_html=True)
