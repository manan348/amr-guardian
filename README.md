# amr-guardian

**AI-assisted antimicrobial resistance (AMR) surveillance dashboard for Pakistan.**

Parses lab reports, visualizes resistance patterns across organisms, antibiotics and cities,
and generates AI-written AMR bulletins — built to support clinical and public health
decision-making in low-resource settings.

---

## Live Demo

Deployed on Hugging Face Spaces — try it without any local setup:

**[Launch amr-guardian on Hugging Face](https://huggingface.co/spaces/manan348/amr-guardian)**

---

## Features

- **Lab Report Parser** — Upload a CSV of isolate results, or paste/upload a free-text lab report that is parsed by an LLM into one row per antibiotic
- **Resistance Heatmaps & Map** — Organism × city heatmap, city bubble map, trend and per-antibiotic summaries (low-sample rates flagged)
- **AI-Generated Bulletins** — City AMR bulletins for a chosen period (7 / 30 / 90 days or all data), written by Llama 3.3 70B via the Groq API
- **Lab Report Interpreter** — Chat assistant that interprets AST results in the context of the dataset
- **Dashboard** — Streamlit UI with sidebar filters (organism, antibiotic, city)

---

## About the sample data

`amr_data.csv` is a **synthetic demo dataset** of 300 isolates. Each organism–antibiotic result
is sampled using national resistance rates from the **WHO GLASS Pakistan 2023** reports, but
**cities and dates are assigned at random** and the Intermediate rate is a fixed 10%.
Organism/antibiotic-level rates are therefore roughly realistic, while city, map and
time-trend patterns are illustrative only. Upload real lab data for actual surveillance.

Rates based on fewer than 30 isolates (CLSI M39 guidance) are flagged in the app.

---

## Project Structure

```
amr-guardian/
├── app.py                              # Streamlit app (dashboard, parser, bulletin, chat)
├── amr_utils.py                        # Pure data helpers shared by app, notebook, pipeline and tests
├── AMR_guardian.ipynb                  # Exploratory notebook: WHO GLASS → demo data → antibiogram → validity check
├── amr_data.csv                        # Synthetic demo dataset (see above), produced by the DVC pipeline
├── data/
│   └── glass_rates_pakistan_2023.csv   # WHO GLASS Pakistan 2023 rates extracted from the WHO exports
├── pipeline/                           # DVC stage scripts (generate_data, antibiogram, validate)
├── dvc.yaml                            # DVC pipeline definition
├── params.yaml                         # Pipeline parameters (rows, seed, cities, min isolates)
├── metrics/                            # Pipeline metrics + plot data (tracked in git)
├── tests/                              # pytest suite (utils, app end-to-end, pipeline, notebook)
├── requirements.txt                    # App dependencies
├── requirements-dev.txt                # + test, notebook and DVC dependencies
└── README.md
```

---

## DVC pipeline

The data pipeline is versioned with [DVC](https://dvc.org) and its outputs are stored on
[DagsHub](https://dagshub.com).

```
data/glass_rates_pakistan_2023.csv ──► generate_data ──► amr_data.csv ──► antibiogram ──► outputs/  + metrics/antibiogram.json
                                                                  └──► validate    ──► metrics/validation.json + metrics/demo_vs_who.csv
```

| Stage | Script | Output |
|---|---|---|
| `generate_data` | `pipeline/generate_data.py` | `amr_data.csv` (kept in git, because the app reads it) |
| `antibiogram` | `pipeline/antibiogram.py` | `outputs/antibiogram_*.csv`, `outputs/antibiogram_heatmap.png` (stored with DVC) |
| `validate` | `pipeline/validate.py` | `metrics/validation.json`, `metrics/demo_vs_who.csv` (demo vs. WHO plot) |

```bash
pip install -r requirements-dev.txt
dvc repro            # re-run only the stages whose inputs or params changed
dvc metrics show     # resistance and validation metrics
dvc plots show       # demo-vs-WHO scatter + antibiogram heatmap
dvc pull             # download the stored outputs from DagsHub
```

Change values in `params.yaml` (e.g. `seed`, `n_rows`) and run `dvc repro` to regenerate the data;
`dvc params diff` and `dvc metrics diff` show what changed. With the default parameters the pipeline
reproduces the committed `amr_data.csv` exactly.

---

## Notebook

`AMR_guardian.ipynb` runs locally from the repo root, or in Google Colab (it clones the repo itself).
It loads the WHO GLASS rates, regenerates `amr_data.csv` (and checks it is identical to the committed
file), builds the antibiogram, and compares the demo rates with the WHO source. To re-parse the raw
WHO exports, put them in `data/glass_raw/`.

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests run offline: a fake Groq client replaces the real API, so no key is needed and no quota is used.

---

## Getting Started

### Prerequisites
- Python 3.9+
- A [Groq API key](https://console.groq.com/keys) (free tier is enough) for the AI features

### Installation

```bash
git clone https://github.com/manan348/amr-guardian.git
cd amr-guardian
pip install -r requirements.txt
```

### Configure the API key

Either set an environment variable:

```bash
export GROQ_API_KEY="your-key"
```

or create `.streamlit/secrets.toml` (already git-ignored):

```toml
GROQ_API_KEY = "your-key"
```

Optional: set `GROQ_MODEL` to use a different Groq model (default `llama-3.3-70b-versatile`).

### Run the App

```bash
streamlit run app.py
```

The dashboard works without a key; only the parser, bulletin and chat need it.

---

## Hugging Face Deployment

amr-guardian is deployed as a **Streamlit Space** on Hugging Face.

### Deploy Your Own Fork

1. Create a free account at [huggingface.co](https://huggingface.co)
2. Go to **Spaces → Create New Space**
3. Choose **Streamlit** as the SDK
4. Push your repo:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/amr-guardian
git push hf main
```

5. Add your `GROQ_API_KEY` as a **Secret** under Space Settings → Variables and Secrets

> **Note:** Never hardcode API keys in `app.py` — always use `st.secrets` or environment variables.

### Notes

- The Space auto-rebuilds on every `git push`
- Each browser session is limited to 20 AI requests to protect the shared API quota
- Uploaded data lives only in the current browser session and is not stored
- If your Space sleeps after inactivity, the first load may take ~30 seconds to wake

---

## Data Format

CSV uploads need one row per isolate–antibiotic test with these columns:

| Column | Description |
|---|---|
| `city` | City of the lab/hospital (map supports Karachi, Lahore, Islamabad, Rawalpindi, Peshawar, Quetta, Faisalabad, Multan) |
| `organism` | Bacterial species name |
| `antibiotic` | Antibiotic tested |
| `result` | `S` / `I` / `R`, or `Susceptible` / `Intermediate` / `Resistant` |
| `date` | Sample collection date (`YYYY-MM-DD`) |

Common alternative column names are recognised automatically
(e.g. `pathogen` → `organism`, `drug` → `antibiotic`, `region`/`hospital` → `city`, `sir` → `result`).

---

## Use Case

Pakistan faces a growing AMR crisis with limited centralized surveillance infrastructure.
**amr-guardian** is designed to help hospital labs and public health teams monitor
resistance trends locally — without requiring expensive commercial platforms.

> For clinical decision support only — AI output is not a prescription and does not replace
> infectious-disease or pharmacy consultation.

---

## Tech Stack

- `Streamlit` — Frontend dashboard
- `Plotly` — Interactive heatmaps, charts and map
- `Pandas` — Data processing
- `Groq API` (Llama 3.3 70B) — Report parsing, bulletins and chat
- `Hugging Face Spaces` — Cloud deployment

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Abdul Manan** · [@manan348](https://github.com/manan348)
