"""Executes AMR_guardian.ipynb top to bottom and checks its key results.
Skipped automatically when the notebook tooling (requirements-dev.txt) is not installed."""

import os

import pytest

nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")
pytest.importorskip("matplotlib")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def executed_notebook():
    nb = nbformat.read(os.path.join(ROOT, "AMR_guardian.ipynb"), as_version=4)
    client = nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                                     resources={"metadata": {"path": ROOT}})
    client.execute()
    return nb


def all_text(nb) -> str:
    chunks = []
    for cell in nb.cells:
        for out in cell.get("outputs", []):
            chunks.append(out.get("text", ""))
            chunks.append(out.get("data", {}).get("text/plain", ""))
    return "".join(chunks)   # a print() can arrive as several stream outputs


def test_notebook_runs_without_errors(executed_notebook):
    errors = [o for c in executed_notebook.cells for o in c.get("outputs", [])
              if o.get("output_type") == "error"]
    assert not errors, errors[0]


def test_notebook_reproduces_demo_dataset(executed_notebook):
    assert "Identical to committed amr_data.csv: True" in all_text(executed_notebook)


def test_notebook_writes_outputs(executed_notebook):
    for name in ["antibiogram_global.csv", "antibiogram_by_city.csv", "antibiogram_heatmap.png"]:
        assert os.path.exists(os.path.join(ROOT, "outputs", "notebook", name)), name
