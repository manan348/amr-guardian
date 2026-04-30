"""
AMR Guardian — Streamlit Dashboard
Save this file to: /content/drive/MyDrive/amr_guardian/app.py

Run in Colab:
    !pip install streamlit pyngrok plotly pandas groq -q
    from pyngrok import ngrok
    import subprocess, threading
    def run():
        subprocess.run(["streamlit", "run",
                        "/content/drive/MyDrive/amr_guardian/app.py",
                        "--server.port=8501"])
    t = threading.Thread(target=run); t.start()
    public_url = ngrok.connect(8501)
    print("AMR Guardian →", public_url)
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMR Guardian",
    page_icon="🧬",
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
    background-color: var(--bg);
    color: var(--text);
}

/* Main header */
.amr-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 28px 0 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
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
    font-size: 0.85rem;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    margin: 0;
}

/* KPI cards */
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
    font-size: 0.72rem;
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

/* Section headings */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    padding-left: 2px;
}

/* Chat */
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
    font-size: 0.875rem;
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

/* Resistance badge row */
.badge-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.badge {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}
.badge.r { background: #3d1515; color: var(--resistant); border: 1px solid #7a2020; }
.badge.s { background: #0d2e26; color: var(--susceptible); border: 1px solid #006655; }
.badge.i { background: #2e2200; color: var(--intermediate); border: 1px solid #664400; }

/* Streamlit overrides */
div[data-testid="stPlotlyChart"] { background: transparent !important; }
.stTextArea textarea {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.875rem !important;
}
.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
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
PLOT_CFG  = dict(paper_bgcolor="rgba(0,0,0,0)",
                 plot_bgcolor="rgba(0,0,0,0)",
                 margin=dict(l=10,r=10,t=30,b=10),
                 font=dict(color="#e2e8f0"))
COLORS    = {"Resistant": "#ff6b6b", "Susceptible": "#00d4aa", "Intermediate": "#ffd166"}

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["result"] = df["result"].str.strip().str.title()
    df["organism"] = df["organism"].str.strip()
    df["city"] = df["city"].str.strip()
    df["antibiotic"] = df["antibiotic"].str.strip()
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
    st.warning(f"⚠️ Data file not found at `{DATA_PATH}`. Using demo data.")
    import numpy as np
    np.random.seed(42)
    orgs = ["Escherichia coli","Klebsiella pneumoniae","Acinetobacter spp.",
            "Salmonella spp.","Streptococcus pneumoniae"]
    abx  = ["Ceftriaxone","Meropenem","Co-trimoxazole","Ampicillin","Ciprofloxacin"]
    cities = ["Karachi","Lahore","Islamabad","Peshawar","Quetta"]
    n = 300
    df = pd.DataFrame({
        "city":      np.random.choice(cities, n),
        "organism":  np.random.choice(orgs, n),
        "antibiotic":np.random.choice(abx, n),
        "result":    np.random.choice(["Resistant","Susceptible","Intermediate"],
                                      n, p=[0.47,0.42,0.11]),
        "date":      pd.date_range("2023-01-01", periods=n, freq="D")[:n],
    })
    data_ok = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="amr-title" style="font-size:1.2rem">🧬 AMR Guardian</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="amr-subtitle">Pakistan Resistance Tracker</p>',
                unsafe_allow_html=True)
    st.markdown("---")

    organisms  = ["All"] + sorted(df["organism"].unique().tolist())
    antibiotics= ["All"] + sorted(df["antibiotic"].unique().tolist())
    cities_list= ["All"] + sorted(df["city"].unique().tolist())

    sel_org  = st.selectbox("Organism",   organisms)
    sel_abx  = st.selectbox("Antibiotic", antibiotics)
    sel_city = st.selectbox("City",       cities_list)

    st.markdown("---")
    st.markdown('<p class="section-title">WHO Reference Rates (PK 2023)</p>',
                unsafe_allow_html=True)
    ref_data = [
        ("Klebsiella + Ceftriaxone", 84),
        ("Strep + Co-trimoxazole",   87),
        ("E. coli + Ceftriaxone",    83),
        ("Acinetobacter + Meropenem",68),
        ("Klebsiella + Meropenem",   59),
        ("Salmonella + Ceftriaxone", 49),
    ]
    for label, rate in ref_data:
        color = "#ff6b6b" if rate >= 70 else "#ffd166" if rate >= 50 else "#00d4aa"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.75rem;padding:4px 0;border-bottom:1px solid #1e2d40">'
            f'<span style="color:#94a3b8">{label}</span>'
            f'<span style="font-family:Space Mono,monospace;font-weight:700;color:{color}">'
            f'{rate}%</span></div>',
            unsafe_allow_html=True,
        )

# ── Filter ────────────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_org   != "All": fdf = fdf[fdf["organism"]   == sel_org]
if sel_abx   != "All": fdf = fdf[fdf["antibiotic"] == sel_abx]
if sel_city  != "All": fdf = fdf[fdf["city"]        == sel_city]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="amr-header">
  <div>
    <p class="amr-title">🧬 AMR Guardian</p>
    <p class="amr-subtitle">Antimicrobial Resistance Surveillance · Pakistan 2023</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI cards ─────────────────────────────────────────────────────────────────
total  = len(fdf)
n_res  = (fdf["result"] == "Resistant").sum()
n_sus  = (fdf["result"] == "Susceptible").sum()
n_int  = (fdf["result"] == "Intermediate").sum()
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
    org_stats = (
        fdf.groupby("organism")["result"]
        .apply(lambda s: round((s == "Resistant").mean() * 100, 1))
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
        xaxis=dict(gridcolor="#1e2d40", ticksuffix="%", range=[0,100]),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=320,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown('<p class="section-title">Resistance Trend Over Time</p>',
                unsafe_allow_html=True)
    trend = (
        fdf.set_index("date")["result"]
        .resample("2W")
        .apply(lambda s: round((s == "Resistant").mean() * 100, 1) if len(s) else None)
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
    cities = sorted(fdf["city"].unique())
    for result_type, color in COLORS.items():
        counts = [
            len(fdf[(fdf["city"] == c) & (fdf["result"] == result_type)])
            for c in cities
        ]
        fig_city.add_trace(go.Bar(
            name=result_type, x=cities, y=counts,
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
    heat = (
        fdf.groupby(["organism","city"])["result"]
        .apply(lambda s: round((s == "Resistant").mean() * 100, 1))
        .unstack(fill_value=0)
    )
    # Short organism labels
    heat.index = (heat.index
        .str.replace("Escherichia coli", "E. coli")
        .str.replace("Klebsiella pneumoniae", "K. pneumoniae")
        .str.replace("Streptococcus pneumoniae", "S. pneumoniae")
    )
    fig_heat = go.Figure(go.Heatmap(
        z=heat.values,
        x=heat.columns.tolist(),
        y=heat.index.tolist(),
        colorscale=[[0,"#0d2e26"],[0.5,"#ffd166"],[1,"#ff6b6b"]],
        zmin=0, zmax=100,
        text=heat.values,
        texttemplate="%{text}%",
        textfont=dict(family="Space Mono", size=11),
        colorbar=dict(ticksuffix="%", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_heat.update_layout(
        **PLOT_CFG,
        xaxis=dict(side="bottom"),
        height=320,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Antibiotic breakdown table ────────────────────────────────────────────────
st.markdown('<p class="section-title">Antibiotic Resistance Summary</p>',
            unsafe_allow_html=True)
abx_summary = (
    fdf.groupby("antibiotic")["result"]
    .value_counts(normalize=True)
    .mul(100).round(1)
    .unstack(fill_value=0)
    .reset_index()
)
# Ensure all columns exist
for col in ["Resistant","Susceptible","Intermediate"]:
    if col not in abx_summary.columns:
        abx_summary[col] = 0.0
abx_summary = abx_summary.rename(columns={"antibiotic": "Antibiotic"})
abx_summary["Total Isolates"] = fdf.groupby("antibiotic").size().values
abx_summary = abx_summary.sort_values("Resistant", ascending=False)

def color_resistant(val):
    if isinstance(val, float):
        if val >= 70: return "color: #ff6b6b; font-weight: 600"
        elif val >= 50: return "color: #ffd166"
        else: return "color: #00d4aa"
    return ""

styled = (
    abx_summary[["Antibiotic","Resistant","Susceptible","Intermediate","Total Isolates"]]
    .style
    .map(color_resistant, subset=["Resistant","Susceptible","Intermediate"])
    .format({"Resistant": "{:.1f}%", "Susceptible": "{:.1f}%", "Intermediate": "{:.1f}%"})
    .set_properties(**{
        "background-color": "#111827",
        "color": "#e2e8f0",
        "border-color": "#1e2d40",
        "font-family": "DM Sans, sans-serif",
        "font-size": "0.875rem",
    })
    .set_table_styles([
        {"selector":"th", "props":[
            ("background-color","#0a0e1a"),
            ("color","#64748b"),
            ("font-family","Space Mono, monospace"),
            ("font-size","0.7rem"),
            ("letter-spacing","1px"),
            ("text-transform","uppercase"),
            ("border-bottom","1px solid #1e2d40"),
        ]},
        {"selector":"tr:hover td", "props":[("background-color","#1a2744")]},
    ])
)
st.dataframe(styled, use_container_width=True, height=220)

# ── Groq Chatbot ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-title">🤖 Lab Report Interpreter — Powered by Groq</p>',
            unsafe_allow_html=True)

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant",
         "content": ("Hello, Doctor. I'm your AMR Guardian assistant.\n\n"
                     "Paste a lab report or ask me about resistance patterns — "
                     "I'll interpret results using WHO Pakistan 2023 resistance data. "
                     "For example: *'Patient has Klebsiella pneumoniae, Ceftriaxone MIC 32 μg/mL'*")}
    ]

# Build system prompt with live data summary
resist_summary = (
    df.groupby("organism")["result"]
    .apply(lambda s: f"{round((s=='Resistant').mean()*100,1)}% resistant")
    .to_dict()
)
system_prompt = f"""You are AMR Guardian, an expert clinical microbiology AI assistant for Pakistani hospitals.
You interpret lab reports and antimicrobial susceptibility test (AST) results, providing actionable clinical guidance.

LIVE DATASET SUMMARY (amr_data.csv, WHO Pakistan 2023):
{chr(10).join(f'  • {k}: {v}' for k,v in resist_summary.items())}

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

# Render chat history
chat_html = '<div class="chat-wrap" id="chat-scroll">'
for msg in st.session_state.chat_history:
    role = msg["role"]
    avatar = "🧬" if role == "assistant" else "👨‍⚕️"
    av_class = "bot" if role == "assistant" else "user-av"
    side = "assistant" if role == "assistant" else "user"
    content = msg["content"].replace("\n","<br>")
    chat_html += f"""
    <div class="msg {side}">
      <div class="avatar {av_class}">{avatar}</div>
      <div class="msg-bubble">{content}</div>
    </div>"""
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# Input area
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
    send = st.button("⬆ SEND", use_container_width=True)

if send and user_input.strip():
    client = get_groq_client()
    if client is None:
        st.error("❌ GROQ_API_KEY not found. Add it to Streamlit → Advanced Settings → Secrets.")
    else:
        st.session_state.chat_history.append({"role":"user","content":user_input.strip()})
        with st.spinner("Analyzing with Groq llama-3.1-70b…"):
            try:
                messages_payload = [{"role":"system","content":system_prompt}] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history
                ]
                response = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=messages_payload,
                    temperature=0.3,
                    max_tokens=700,
                )
                reply = response.choices[0].message.content
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()
            except Exception as e:
                st.error(f"Groq API error: {e}")

if st.button("🗑 Clear Chat", key="clear_chat"):
    st.session_state.chat_history = st.session_state.chat_history[:1]
    st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2d40;
            display:flex;justify-content:space-between;align-items:center">
  <span style="font-family:Space Mono,monospace;font-size:0.7rem;color:#334155">
    AMR Guardian · WHO GLASS Pakistan 2023 · Built with Streamlit + Groq
  </span>
  <span style="font-family:Space Mono,monospace;font-size:0.7rem;color:#334155">
    ⚠ For clinical decision support only — not a substitute for ID consultation
  </span>
</div>
""", unsafe_allow_html=True)
