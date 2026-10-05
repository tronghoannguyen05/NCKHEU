"""Build the analysis panels from raw and hand-coded files.

Outputs (data/processed/):
- countries.csv: one row per sample country with cohorts, baseline covariates, safeguards, design features
- panel_country_year.csv: SDG 1.3.1 and placebo outcomes, 2014-2024
- panel_country_wave.csv: Findex transfer receipt by group and the within-country gaps

Usage: python -m idsp.data.panel
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..coding import validate_rollout
from ..gaps import add_gaps
from ..safeguards import safeguard_index
from ..treatment import annual_cohort, wave_cohort


def read_manual(name: str, sources: dict) -> pd.DataFrame:
    spec = sources["manual"][name]
    path = config.MANUAL / spec["file"]
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. See docs/data_sources.md ({name}).")
    df = pd.read_csv(path)
    missing = [c for c in spec["schema"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}; expected schema {spec['schema']}")
    return df[spec["schema"]]


def read_wb(name: str) -> pd.DataFrame:
    path = config.RAW / f"wb_{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python -m idsp.data.worldbank` first.")
    return pd.read_csv(path).rename(columns={"value": name})


def baseline(long: pd.DataFrame, var: str, year: int, lookback: int) -> pd.Series:
    """Latest non-missing value of var in [year - lookback, year], by iso3."""
    d = long[(long["year"] <= year) & (long["year"] >= year - lookback)].dropna(subset=[var])
    return d.sort_values("year").groupby("iso3")[var].last()


def build(settings: dict | None = None, sources: dict | None = None) -> dict:
    s = settings or config.load("settings")
    src = sources or config.load("sources")
    by, lb = s["baseline"]["year"], s["baseline"]["lookback_years"]

    countries = read_manual("income_classification", src)
    countries = countries[countries["income_group"].isin(s["sample"]["income_groups"])].copy()

    roll = pd.read_csv(config.ROOT / src["hand_coded"]["rollout"])
    problems = validate_rollout(roll)
    if len(problems):
        raise ValueError(f"Rollout coding has problems:\n{problems.to_string(index=False)}")
    if roll["iso3"].duplicated().any():
        raise ValueError("rollout_coding.csv must hold one reconciled row per country.")
    draft = roll[roll["status"].astype(str).str.lower() != "final"]
    if len(draft):
        print(f"WARNING: {len(draft)} rollout rows are not final: {', '.join(draft['iso3'])}")
    keep = ["iso3", "rollout_year", "rollout_year_alt", "biometric_enrolment",
            "biometric_auth_mandatory_benefits", "non_biometric_fallback", "donor_financed"]
    countries = countries.merge(roll[[c for c in keep if c in roll.columns]], on="iso3", how="left")

    dp = pd.read_csv(config.ROOT / src["hand_coded"]["dp_law"])[["iso3", "dp_law_year"]]
    countries = countries.merge(dp, on="iso3", how="left")

    wb = {n: read_wb(n) for n in ["gdppc_ppp", "urban", "mobile", "battle_deaths", "elec_access",
                                  "agri_land", "wgi_va", "wgi_rl"]}
    countries["log_gdppc_2014"] = countries["iso3"].map(np.log(baseline(wb["gdppc_ppp"], "gdppc_ppp", by, lb)))
    countries["urban_2014"] = countries["iso3"].map(baseline(wb["urban"], "urban", by, lb))
    countries["mobile_2014"] = countries["iso3"].map(baseline(wb["mobile"], "mobile", by, lb))
    bd = wb["battle_deaths"]
    conflict = bd[(bd["year"] >= by - lb) & (bd["year"] <= by)].groupby("iso3")["battle_deaths"].max() >= 25
    countries["conflict_2010_2014"] = countries["iso3"].map(conflict).fillna(False).astype(float)
    countries["wgi_va_2014"] = countries["iso3"].map(baseline(wb["wgi_va"], "wgi_va", by, lb))
    countries["wgi_rl_2014"] = countries["iso3"].map(baseline(wb["wgi_rl"], "wgi_rl", by, lb))
    vdem = read_manual("vdem", src)
    countries["vdem_cspart_2014"] = countries["iso3"].map(baseline(vdem, "v2x_cspart", by, lb))
    try:
        sp = read_manual("sp_spending", src)
        countries["sp_spending_2014"] = countries["iso3"].map(baseline(sp, "sp_spending", by, lb))
    except FileNotFoundError:
        countries["sp_spending_2014"] = np.nan

    sg = safeguard_index(countries, s["safeguards"]["components"], by, s["safeguards"]["dp_law_col"],
                         s["safeguards"]["split"])
    countries = countries.merge(sg[["iso3", "safeguard", "high_safeguard"]], on="iso3", how="left")

    a, w = s["annual"], s["waves"]
    countries["cohort_annual"] = annual_cohort(countries["rollout_year"], a["rollout_lag_years"])
    countries["cohort_wave"] = [wave_cohort(r, w["years"], w["rollout_lag_years"]) for r in countries["rollout_year"]]

    years = range(a["first_year"], a["last_year"] + 1)
    cy = pd.MultiIndex.from_product([countries["iso3"], years], names=["iso3", "year"]).to_frame(index=False)
    cy = cy.merge(read_manual("sdg131", src), on=["iso3", "year"], how="left")
    for n in ["elec_access", "agri_land"]:
        cy = cy.merge(wb[n], on=["iso3", "year"], how="left")
    cy = cy.merge(countries, on="iso3", how="left")

    fx = add_gaps(read_manual("findex", src))
    cw = pd.MultiIndex.from_product([countries["iso3"], w["years"]], names=["iso3", "wave"]).to_frame(index=False)
    cw = cw.merge(fx, on=["iso3", "wave"], how="left").merge(countries, on="iso3", how="left")

    for df, keys in [(cy, ["iso3", "year"]), (cw, ["iso3", "wave"])]:
        if df.duplicated(keys).any():
            raise ValueError(f"Duplicate keys {keys} in panel.")
    pct = ["sdg131_total"] + [c for c in cw.columns if c.startswith("transfer_")]
    for c in pct:
        frame = cy if c in cy else cw
        bad = frame[c].dropna().pipe(lambda v: v[(v < 0) | (v > 100)])
        if len(bad):
            raise ValueError(f"{c} has values outside 0-100.")

    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    countries.to_csv(config.PROCESSED / "countries.csv", index=False)
    cy.to_csv(config.PROCESSED / "panel_country_year.csv", index=False)
    cw.to_csv(config.PROCESSED / "panel_country_wave.csv", index=False)
    print(f"countries={len(countries)} country-years={len(cy)} country-waves={len(cw)} -> data/processed/")
    return dict(countries=countries, country_year=cy, country_wave=cw)


if __name__ == "__main__":
    build()
