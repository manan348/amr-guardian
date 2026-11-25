"""Stage 2: antibiogram tables + heatmap from amr_data.csv."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import amr_utils
from pipeline.common import DEMO_CSV, METRICS, OUTPUTS, load_params, write_json


def main() -> None:
    min_n = load_params()["antibiogram"]["min_isolates"]
    df, _ = amr_utils.clean_records(pd.read_csv(DEMO_CSV))
    OUTPUTS.mkdir(exist_ok=True)

    pairs = amr_utils.rate_table(df, ["organism", "antibiotic"])
    rates, counts = pairs["rate"].unstack(), pairs["n"].unstack()
    rates.to_csv(OUTPUTS / "antibiogram_global.csv")
    counts.reindex_like(rates).to_csv(OUTPUTS / "antibiogram_counts.csv")
    amr_utils.rate_table(df, ["city", "organism", "antibiotic"]).to_csv(OUTPUTS / "antibiogram_by_city.csv")

    fig, ax = plt.subplots(figsize=(12, 4.5))
    im = ax.imshow(rates.values, cmap="RdYlGn_r", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(rates.columns)), rates.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(rates.index)), rates.index)
    counts = counts.reindex_like(rates)
    for i in range(rates.shape[0]):
        for j in range(rates.shape[1]):
            v, n = rates.iat[i, j], counts.iat[i, j]
            if not pd.isna(v):
                ax.text(j, i, f"{v:.0f}%\nn={int(n)}", ha="center", va="center", fontsize=8,
                        alpha=0.45 if n < min_n else 1.0)
    fig.colorbar(im, ax=ax, label="% resistant")
    ax.set_title(f"Antibiogram (faded = n < {min_n})")
    fig.tight_layout()
    fig.savefig(OUTPUTS / "antibiogram_heatmap.png", dpi=150)
    plt.close(fig)

    write_json(METRICS / "antibiogram.json", {
        "n_isolates": int(len(df)),
        "n_pairs": int(len(pairs)),
        "pairs_below_min_isolates": int((pairs["n"] < min_n).sum()),
        "overall_resistance_rate": amr_utils.resistance_rate(df["result"]),
    })
    print(f"Antibiogram: {len(pairs)} organism-antibiotic pairs from {len(df)} isolates")


if __name__ == "__main__":
    main()
