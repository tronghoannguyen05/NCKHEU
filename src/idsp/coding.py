"""Hand-coded rollout dataset: validation, second-coder sample and inter-coder agreement.

Rules (docs/coding_protocol.md):
- every final rollout year needs at least two independent sources;
- a random 20% of countries is coded independently by a second coder;
- agreement is reported as exact-year agreement, agreement within one year, mean absolute
  difference, and Cohen's kappa for binary design features.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED = ["iso3", "country", "coder", "digital_id_system", "rollout_year", "rollout_event",
            "source1_citation", "source1_url", "source2_citation", "source2_url", "status"]
BINARY_FEATURES = ["biometric_enrolment", "biometric_auth_mandatory_benefits",
                   "non_biometric_fallback", "linked_social_registry", "donor_financed"]


def validate_rollout(df: pd.DataFrame, min_year=1990, max_year=2024) -> pd.DataFrame:
    """Return one row per problem found (empty frame = no problems)."""
    problems = []
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return pd.DataFrame([{"iso3": None, "problem": f"missing columns: {missing}"}])
    dup = df.duplicated(["iso3", "coder"], keep=False)
    for _, r in df[dup].iterrows():
        problems.append({"iso3": r["iso3"], "problem": "duplicate iso3 for the same coder"})
    for _, r in df.iterrows():
        y = pd.to_numeric(r["rollout_year"], errors="coerce")
        never = str(r.get("rollout_event", "")).strip().lower() == "none"
        if not never and not np.isfinite(y):
            problems.append({"iso3": r["iso3"], "problem": "rollout_year missing (use rollout_event='none' if no digital ID)"})
        if np.isfinite(y) and not (min_year <= y <= max_year):
            problems.append({"iso3": r["iso3"], "problem": f"rollout_year {y} outside {min_year}-{max_year}"})
        if str(r["status"]).strip().lower() == "final":
            urls = {str(r[c]).strip().lower() for c in ["source1_url", "source2_url"]
                    if pd.notna(r[c]) and str(r[c]).strip()}
            if len(urls) < 2:
                problems.append({"iso3": r["iso3"], "problem": "final coding needs two distinct sources"})
        for f in BINARY_FEATURES:
            if f in df.columns and pd.notna(r[f]) and r[f] not in (0, 1, "0", "1"):
                problems.append({"iso3": r["iso3"], "problem": f"{f} must be 0, 1 or blank"})
    return pd.DataFrame(problems, columns=["iso3", "problem"])


def second_coder_sample(iso3: list[str], frac: float = 0.2, seed: int = 20261004) -> list[str]:
    """Reproducible random sample of countries for independent double coding."""
    iso3 = sorted(set(iso3))
    k = int(np.ceil(frac * len(iso3)))
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(iso3, size=k, replace=False).tolist())


def cohen_kappa(a, b) -> float:
    a, b = pd.Series(a), pd.Series(b)
    ok = a.notna() & b.notna()
    a, b = a[ok].astype(str), b[ok].astype(str)
    if len(a) == 0:
        return np.nan
    cats = sorted(set(a) | set(b))
    po = (a.to_numpy() == b.to_numpy()).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def agreement(primary: pd.DataFrame, second: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agreement statistics between the primary coding and the second coder.

    Returns (summary table, list of disagreements to resolve).
    """
    m = primary.merge(second, on="iso3", suffixes=("_1", "_2"))
    y1 = pd.to_numeric(m["rollout_year_1"], errors="coerce")
    y2 = pd.to_numeric(m["rollout_year_2"], errors="coerce")
    both = y1.notna() & y2.notna()
    none1 = m["rollout_event_1"].astype(str).str.lower().eq("none")
    none2 = m["rollout_event_2"].astype(str).str.lower().eq("none")
    rows = [
        ("countries double-coded", len(m)),
        ("agree on having a digital ID (yes/no)", float(((y1.notna() | ~none1) == (y2.notna() | ~none2)).mean())),
        ("exact rollout-year agreement", float((y1[both] == y2[both]).mean()) if both.any() else np.nan),
        ("agreement within one year", float(((y1[both] - y2[both]).abs() <= 1).mean()) if both.any() else np.nan),
        ("mean absolute difference (years)", float((y1[both] - y2[both]).abs().mean()) if both.any() else np.nan),
    ]
    for f in BINARY_FEATURES:
        if f"{f}_1" in m and f"{f}_2" in m:
            rows.append((f"Cohen's kappa: {f}", cohen_kappa(m[f"{f}_1"], m[f"{f}_2"])))
    summary = pd.DataFrame(rows, columns=["statistic", "value"])
    agree = (both & (y1 == y2)) | (none1 & none2)
    dis = m.loc[~agree, ["iso3", "rollout_year_1", "rollout_year_2", "rollout_event_1", "rollout_event_2"]]
    return summary, dis.reset_index(drop=True)


def main(argv=None):
    import argparse

    from . import config

    ap = argparse.ArgumentParser(description="Hand-coded rollout dataset tools")
    ap.add_argument("command", choices=["validate", "sample", "agreement"])
    ap.add_argument("--frac", type=float, default=0.2)
    args = ap.parse_args(argv)
    src = config.load("sources")["hand_coded"]
    primary = pd.read_csv(config.ROOT / src["rollout"])
    if args.command == "validate":
        p = validate_rollout(primary)
        print("No problems." if p.empty else p.to_string(index=False))
    elif args.command == "sample":
        s = config.load("settings")
        print("\n".join(second_coder_sample(primary["iso3"].tolist(), args.frac, s["seed"])))
    else:
        second = pd.read_csv(config.ROOT / src["rollout_second_coder"])
        summary, dis = agreement(primary, second)
        print(summary.to_string(index=False))
        if len(dis):
            print("\nDisagreements to resolve:\n" + dis.to_string(index=False))


if __name__ == "__main__":
    main()
