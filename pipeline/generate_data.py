"""Stage 1: WHO GLASS rates -> synthetic isolate-level demo dataset (amr_data.csv)."""

import pandas as pd

import amr_utils
from pipeline.common import DEMO_CSV, GLASS_CSV, load_params


def main() -> None:
    p = load_params()["data"]
    glass = pd.read_csv(GLASS_CSV)
    demo = amr_utils.generate_demo_data(
        glass,
        n_rows=p["n_rows"],
        cities=p["cities"],
        seed=p["seed"],
        intermediate_share=p["intermediate_share"],
    )
    demo.to_csv(DEMO_CSV, index=False, lineterminator="\n")
    print(f"Wrote {len(demo)} rows to {DEMO_CSV.name}")


if __name__ == "__main__":
    main()
