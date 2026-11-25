"""Stage 3: compare the demo dataset's resistance rates with the WHO GLASS source rates."""

import pandas as pd

import amr_utils
from pipeline.common import DEMO_CSV, GLASS_CSV, METRICS, write_json


def main() -> None:
    df, _ = amr_utils.clean_records(pd.read_csv(DEMO_CSV))
    glass = pd.read_csv(GLASS_CSV)
    cmp = amr_utils.compare_with_reference(df, glass)

    METRICS.mkdir(exist_ok=True)
    cmp.to_csv(METRICS / "demo_vs_who.csv", index=False, lineterminator="\n")
    worst = cmp.iloc[0]
    write_json(METRICS / "validation.json", {
        "n_pairs": int(len(cmp)),
        "median_abs_diff_pp": round(float(cmp["abs_diff"].median()), 1),
        "max_abs_diff_pp": float(worst["abs_diff"]),
        "max_abs_diff_pair": f"{worst['organism']} / {worst['antibiotic']}",
        "pairs_reference_inside_ci": int(cmp["reference_inside_ci"].sum()),
    })
    print(f"Validation: median |diff| {cmp['abs_diff'].median():.1f} pp over {len(cmp)} pairs")


if __name__ == "__main__":
    main()
