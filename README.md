# amr-guardian 🦠🛡️

**AI-powered antimicrobial resistance (AMR) surveillance platform for Pakistan.**

Parses lab reports, visualizes resistance heatmaps across pathogens and antibiotics,
and generates AI-written weekly AMR bulletins — built to support clinical and
public health decision-making in low-resource settings.

---

## 🚀 Live Demo

Deployed on Hugging Face Spaces — try it without any local setup:

👉 **[Launch amr-guardian on Hugging Face](https://huggingface.co/spaces/manan348/amr-guardian)**

---

## Features

- 📄 **Lab Report Parser** — Upload CSV-based lab data and extract resistance profiles
- 🗺️ **Resistance Heatmaps** — Interactive visualizations of pathogen × antibiotic resistance rates
- 🤖 **AI-Generated Bulletins** — Weekly AMR summaries auto-written using Claude AI
- 📊 **Dashboard** — Streamlit-powered UI with sidebar navigation and chatbot interface

---

## Project Structure

```
amr-guardian/
├── app.py                   # Streamlit frontend
├── AMR_guardian.ipynb       # Data analysis & model notebook
├── amr_data.csv             # Sample AMR dataset
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/manan348/amr-guardian.git
cd amr-guardian
pip install -r requirements.txt
```

### Run the App

```bash
streamlit run app.py
```

---

## ☁️ Hugging Face Deployment

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

5. Add your `ANTHROPIC_API_KEY` as a **Secret** under Space Settings → Variables and Secrets

> ⚠️ Never hardcode API keys in `app.py` — always use `st.secrets` or environment variables.

### Hugging Face–Specific Notes

- The Space auto-rebuilds on every `git push`
- Keep `requirements.txt` up to date — HF installs from it on each build
- If your Space sleeps after inactivity, the first load may take ~30 seconds to wake

---

## Data Format

The platform expects `amr_data.csv` with columns such as:

| Column | Description |
|---|---|
| `pathogen` | Bacterial species name |
| `antibiotic` | Antibiotic tested |
| `result` | S / I / R (Sensitive/Intermediate/Resistant) |
| `region` | City or hospital region (Pakistan) |
| `date` | Sample collection date |

*(Adjust based on your actual schema)*

---

## Use Case

Pakistan faces a growing AMR crisis with limited centralized surveillance infrastructure.
**amr-guardian** is designed to help hospital labs and public health teams monitor
resistance trends locally — without requiring expensive commercial platforms.

---

## Tech Stack

- `Streamlit` — Frontend dashboard
- `Plotly` — Interactive heatmaps and charts
- `Pandas` — Data processing
- `Anthropic Claude API` — AI bulletin generation
- `Hugging Face Spaces` — Cloud deployment

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Abdul Manan** · [@manan348](https://github.com/manan348)
