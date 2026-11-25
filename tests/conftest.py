"""Shared pytest fixtures. A fake `groq` module stands in for the real API so the
app can be tested offline, without a key and without spending quota."""

import json
import os
import sys
import types
from types import SimpleNamespace as NS

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class FakeGroq:
    """Records every request; answers depend on which feature sent the prompt."""
    calls: list = []
    parse_reply = json.dumps([
        {"organism": "Klebsiella pneumoniae", "antibiotic": "Ceftriaxone",
         "result": "R", "city": "Lahore", "date": None},
        {"organism": "Klebsiella pneumoniae", "antibiotic": "Meropenem",
         "result": "Susceptible", "city": "Lahore", "date": "2024-03-15"},
        {"organism": "Klebsiella pneumoniae", "antibiotic": "Unknown drug",
         "result": "maybe", "city": "Lahore", "date": "2024-03-15"},
    ])
    bulletin_reply = "## EXECUTIVE SUMMARY\n**Bold** text <img src=x onerror=alert(1)>"
    chat_reply = "Reply <b>html</b>"

    def __init__(self, api_key):
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, model, messages, **kwargs):
        FakeGroq.calls.append({"model": model, "messages": messages})
        prompt = messages[-1]["content"]
        if "data extractor" in prompt:
            text = FakeGroq.parse_reply
        elif "bulletin" in prompt:
            text = FakeGroq.bulletin_reply
        else:
            text = FakeGroq.chat_reply
        return NS(choices=[NS(message=NS(content=text))])


@pytest.fixture
def fake_groq(monkeypatch):
    module = types.ModuleType("groq")
    module.Groq = FakeGroq
    monkeypatch.setitem(sys.modules, "groq", module)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    FakeGroq.calls = []
    return FakeGroq


@pytest.fixture
def app(fake_groq, monkeypatch):
    """A freshly loaded app (Streamlit AppTest) running against the fake Groq client."""
    from streamlit.testing.v1 import AppTest
    monkeypatch.chdir(ROOT)
    at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at
