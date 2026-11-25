"""End-to-end tests of app.py using Streamlit's AppTest and a fake Groq client
(see conftest.py). They run offline and never call the real API."""

import io
import json
import re

import pandas as pd
import pytest


def kpi_total(at) -> int:
    for m in at.markdown:
        if "Total Isolates</div>" in m.value:
            return int(re.search(r'kpi-value white">([\d,]+)<', m.value).group(1).replace(",", ""))
    raise AssertionError("KPI card not found")


def button(at, label):
    return next(b for b in at.button if b.label == label)


# ── Dashboard ────────────────────────────────────────────────────────────────
def test_app_loads_with_demo_data(app):
    assert kpi_total(app) == 300
    df = app.session_state.working_df
    assert df["result"].isin(["Resistant", "Susceptible", "Intermediate"]).all()
    assert any("Demo dataset" in i.value for i in app.info)


def test_map_shows_every_city(app):
    specs = [json.loads(c.proto.spec) for c in app.get("plotly_chart")]
    geo = next(s for s in specs if s["data"][0]["type"] == "scattergeo")
    assert len(geo["data"][0]["lat"]) == app.session_state.working_df["city"].nunique() == 8


def test_sidebar_filter_updates_kpis(app):
    app.sidebar.selectbox[2].select("Lahore").run()   # City filter
    df = app.session_state.working_df
    assert kpi_total(app) == (df["city"] == "Lahore").sum()


# ── Uploads ──────────────────────────────────────────────────────────────────
class FakeUpload(io.BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name, self.size = name, len(data)


@pytest.fixture
def csv_upload(monkeypatch):
    """Make st.file_uploader return a CSV that uses alias column names and S/I/R codes."""
    import streamlit as st
    data = ("Region,Pathogen,Drug,SIR,collection_date\n"
            "Lahore,E. coli,Ceftriaxone,R,2024-01-02\n"
            "Multan,E. coli,Meropenem,S,2024-01-03\n"
            "Multan,E. coli,Meropenem,?,2024-01-03\n").encode("utf-8-sig")
    monkeypatch.setattr(st, "file_uploader", lambda *a, **k: FakeUpload(data, "lab.csv"))


def test_csv_upload_merges_once(fake_groq, csv_upload, monkeypatch):
    from streamlit.testing.v1 import AppTest
    import conftest
    monkeypatch.chdir(conftest.ROOT)
    at = AppTest.from_file("app.py", default_timeout=60)
    at.run()
    at.button(key="parse_report_btn").click().run()
    assert not at.exception, at.exception
    assert len(at.session_state.working_df) == 302                 # 2 valid rows, 1 skipped
    assert any("1 row(s) skipped" in w.value for w in at.warning)

    for _ in range(3):                                             # plain reruns
        at.run()
    at.button(key="parse_report_btn").click().run()                # second click
    assert len(at.session_state.working_df) == 302
    assert any("already been added" in i.value for i in at.info)
    assert fake_groq.calls == []                                   # CSVs never hit the API


def test_text_report_parse_adds_valid_rows(app, fake_groq):
    app.text_area(key="lab_text_input").set_value("Organism: K. pneumoniae\nCeftriaxone: R\nMeropenem: S")
    app.button(key="parse_report_btn").click().run()
    assert not app.exception, app.exception
    df = app.session_state.working_df
    assert len(df) == 302
    assert df["date"].notna().all()
    assert any("1 extracted result(s) skipped" in w.value for w in app.warning)
    for _ in range(2):
        app.run()
    assert len(app.session_state.working_df) == 302


def test_parse_without_input_warns(app, fake_groq):
    app.button(key="parse_report_btn").click().run()
    assert any("paste a lab report" in w.value for w in app.warning)
    assert fake_groq.calls == []


# ── Bulletin ─────────────────────────────────────────────────────────────────
def test_bulletin_renders_markdown_safely(app, fake_groq):
    app.button(key="gen_bulletin_btn").click().run()
    assert not app.exception, app.exception
    md = [m.value for m in app.markdown]
    assert any(v.startswith("## EXECUTIVE SUMMARY") for v in md)   # plain markdown, not raw HTML
    prompt = fake_groq.calls[-1]["messages"][-1]["content"]
    assert "PERIOD:" in prompt and "n=" in prompt


def test_bulletin_period_filters_data(app, fake_groq):
    app.selectbox(key="bulletin_window").select("Last 7 days")
    app.button(key="gen_bulletin_btn").click().run()
    prompt = fake_groq.calls[-1]["messages"][-1]["content"]
    n_week = int(re.search(r"TOTAL ISOLATES: (\d+)", prompt).group(1))

    app.selectbox(key="bulletin_window").select("All data")
    app.button(key="gen_bulletin_btn").click().run()
    prompt = fake_groq.calls[-1]["messages"][-1]["content"]
    n_all = int(re.search(r"TOTAL ISOLATES: (\d+)", prompt).group(1))

    city = app.selectbox(key="bulletin_city").value
    assert n_all == (app.session_state.working_df["city"] == city).sum()
    assert n_week < n_all


# ── Chat ─────────────────────────────────────────────────────────────────────
def test_chat_escapes_html_and_clears_input(app, fake_groq):
    app.text_area(key="chat_input").set_value("<b>test</b><img src=x>")
    button(app, "SEND").click().run()
    assert not app.exception, app.exception
    chat = next(m.value for m in app.markdown if "chat-scroll" in m.value)
    assert "&lt;b&gt;test&lt;/b&gt;&lt;img src=x&gt;" in chat and "<img src=x>" not in chat
    assert "Reply &lt;b&gt;html&lt;/b&gt;" in chat
    assert app.text_area(key="chat_input").value == ""


def test_chat_sends_only_recent_history(app, fake_groq):
    app.session_state.chat_history = (
        app.session_state.chat_history
        + [{"role": r, "content": f"m{i}"} for i in range(30) for r in ("user", "assistant")]
    )
    app.text_area(key="chat_input").set_value("latest question")
    button(app, "SEND").click().run()
    sent = fake_groq.calls[-1]["messages"]
    assert sent[0]["role"] == "system"
    assert len(sent) == 1 + 10
    assert sent[-1]["content"] == "latest question"


# ── Quota / missing key ──────────────────────────────────────────────────────
def test_ai_quota_blocks_extra_calls(app, fake_groq):
    app.session_state.ai_calls = 20
    app.button(key="gen_bulletin_btn").click().run()
    assert any("limit reached" in e.value for e in app.error)
    assert fake_groq.calls == []


def test_missing_api_key_shows_clean_error(fake_groq, monkeypatch):
    from streamlit.testing.v1 import AppTest
    import conftest
    monkeypatch.delenv("GROQ_API_KEY")
    monkeypatch.chdir(conftest.ROOT)
    at = AppTest.from_file("app.py", default_timeout=60)
    at.run()
    at.button(key="gen_bulletin_btn").click().run()
    assert not at.exception
    assert any("GROQ_API_KEY not found" in e.value for e in at.error)
