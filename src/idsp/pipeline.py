"""End-to-end analysis following docs/analysis_plan.md.

    python -m idsp.pipeline --synthetic      # synthetic data, no downloads needed
    python -m idsp.pipeline                  # real data from data/processed/ (python -m idsp.data.panel)

Outputs: output/tables/*.csv, output/figures/*.png, output/honestdid/*.json, output/summary.md.
Every table carries a "data" column (SYNTHETIC or REAL).
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from . import config
from .estimators import cs, dcdh, diagnostics, sunab, twfe, wildboot
from .gaps import add_gaps
from .report.outputs import event_study_plot, honestdid_export, write_table
from .safeguards import safeguard_index
from .synthetic import make_synthetic
from .treatment import annual_cohort, cohort_table, wave_cohort

UNIT = "iso3"


def load_data(s: dict, synthetic: bool):
    if synthetic:
        d = make_synthetic(n_countries=120, waves=tuple(s["waves"]["years"]),
                           wave_lag_years=s["waves"]["rollout_lag_years"], seed=s["seed"])
        countries = d["countries"]
        sg = safeguard_index(countries, s["safeguards"]["components"], s["baseline"]["year"],
                             s["safeguards"]["dp_law_col"], s["safeguards"]["split"])
        countries = countries.merge(sg[["iso3", "safeguard", "high_safeguard"]], on="iso3")
        countries["cohort_annual"] = annual_cohort(countries["rollout_year"], s["annual"]["rollout_lag_years"])
        cy = d["country_year"].drop(columns=["cohort_annual"]).merge(
            countries[["iso3", "safeguard", "high_safeguard", "cohort_annual"]], on="iso3")
        cw = add_gaps(d["country_wave"]).merge(countries[["iso3", "safeguard", "high_safeguard"]], on="iso3")
        return cy, cw, countries
    p = config.PROCESSED
    return (pd.read_csv(p / "panel_country_year.csv"), pd.read_csv(p / "panel_country_wave.csv"),
            pd.read_csv(p / "countries.csv"))


class Runner:
    def __init__(self, s, label, n_boot):
        self.s, self.label, self.n_boot = s, label, n_boot
        self.rows, self.notes = [], []
        self.tables = config.OUTPUT / "tables"
        self.figs = config.OUTPUT / "figures"

    def cs(self, df, y, time, cohort, covariates=None, **kw):
        est = self.s["estimation"]
        covariates = list(covariates or [])
        d = df
        if covariates:
            miss = [c for c in covariates if c not in df.columns]
            if miss:
                raise KeyError(f"Covariates missing from panel: {miss}")
            ok = df[covariates].notna().all(axis=1)
            dropped = df.loc[~ok, UNIT].nunique()
            if dropped:
                self.notes.append(f"{y}: {dropped} countries dropped for missing covariates")
            d = df[ok]
        args = dict(control_group=est["control_group"], base_period=est["base_period"],
                    anticipation=est["anticipation"], n_boot=self.n_boot, alpha=est["alpha"],
                    seed=self.s["seed"], min_treated=est["min_treated"], min_control=est["min_control"])
        args.update(kw)
        return cs.att_gt(d, y, UNIT, time, cohort, covariates=covariates, **args)

    def record(self, analysis, outcome, spec, res=None, **extra):
        row = dict(analysis=analysis, outcome=outcome, spec=spec)
        if res is not None:
            o = res.overall.iloc[0]
            row.update(att=o["att"], se=o["se"], ci_low=o["ci_low"], ci_high=o["ci_high"],
                       p_value=o["p_value"], n_units=res.info["n_units"],
                       n_cohorts=res.info["n_cohorts"], n_always_treated_dropped=res.info["n_always_treated_dropped"])
        row.update(extra)
        self.rows.append(row)
        return row

    def safe(self, fn, *a, label="", **kw):
        try:
            return fn(*a, **kw)
        except (ValueError, KeyError, np.linalg.LinAlgError) as ex:
            self.notes.append(f"{label}: not estimable ({ex})")
            return None

    def write(self, df, name):
        write_table(df, self.tables / f"{name}.csv", self.label)


def recohort(df, s, kind, lag=None, col="rollout_year"):
    d = df.copy()
    if kind == "annual":
        d["cohort_annual"] = annual_cohort(d[col], s["annual"]["rollout_lag_years"] if lag is None else lag)
    else:
        lag = s["waves"]["rollout_lag_years"] if lag is None else lag
        d["cohort_wave"] = [wave_cohort(r, s["waves"]["years"], lag) for r in d[col]]
    return d


def interpolate_inside(df, y, time):
    """Linear interpolation of y within each country's observed range (no extrapolation)."""
    d = df.sort_values([UNIT, time]).copy()
    d[y] = d.groupby(UNIT)[y].transform(lambda v: v.interpolate(limit_area="inside"))
    return d


def run(synthetic: bool = False, n_boot: int | None = None):
    s = config.load("settings")
    label = "SYNTHETIC" if synthetic else "REAL"
    R = Runner(s, label, n_boot or s["estimation"]["n_boot"])
    cy, cw, countries = load_data(s, synthetic)
    est, out = s["estimation"], s["outcomes"]
    covs = est["covariates_main"]
    a, w = s["annual"], s["waves"]
    panels = {"sdg131_total": (cy, "year", "cohort_annual", "annual"),
              out["group_total"]: (cw, "wave", "cohort_wave", "waves")}

    # Descriptives: cohort sizes
    R.write(cohort_table(cy.drop_duplicates(UNIT), "cohort_annual", a["first_year"], a["last_year"]), "cohorts_annual")
    R.write(cohort_table(cw.drop_duplicates(UNIT), "cohort_wave", w["years"][0], w["years"][-1]), "cohorts_waves")

    # H1: average effect
    main = {}
    for y, (df, t, g, kind) in panels.items():
        res = R.safe(R.cs, df, y, t, g, covs, label=f"H1 {y}")
        if res is None:
            continue
        main[y] = res
        R.record("H1", y, "main: OR baseline covariates, not-yet-treated", res,
                 pretrend_p=diagnostics.pretrend_wald(res)["p_value"])
        R.write(res.attgt, f"H1_{y}_attgt")
        R.write(res.dynamic, f"H1_{y}_event_study_varying")
        uni = R.safe(R.cs, df, y, t, g, covs, base_period="universal", label=f"H1 {y} universal")
        if uni is not None:
            R.write(uni.dynamic, f"H1_{y}_event_study_universal")
            xl = "Years since rollout" if kind == "annual" else "Findex waves since rollout"
            event_study_plot(uni.dynamic, R.figs / f"H1_{y}_event_study.png", f"H1: {y}", label, xl,
                             tuple(a["event_window"]) if kind == "annual" else None)
            try:
                honestdid_export(uni, config.OUTPUT / "honestdid" / f"H1_{y}.json",
                                 s["honestdid"]["post_average_e"], label)
            except ValueError as ex:
                R.notes.append(f"HonestDiD export {y}: {ex}")

    # H2: distributional effect on within-country gaps (Holm across gaps)
    h2 = []
    for gap in out["gaps"]:
        if gap not in cw.columns:
            R.notes.append(f"H2 {gap}: column missing")
            continue
        res = R.safe(R.cs, cw, gap, "wave", "cohort_wave", covs, label=f"H2 {gap}")
        if res is not None:
            h2.append(R.record("H2", gap, "main", res))
            R.write(res.dynamic, f"H2_{gap}_event_study")
    if h2:
        adj = multipletests([r["p_value"] for r in h2], method="holm")[1]
        for r, p in zip(h2, adj):
            r["p_adjusted"], r["adjustment"] = p, "holm (H2)"
    for grp in out["groups"]:
        if grp in cw.columns:
            res = R.safe(R.cs, cw, grp, "wave", "cohort_wave", covs, label=f"H2 group {grp}")
            if res is not None:
                R.record("H2 (descriptive)", grp, "group-specific ATT", res)

    # H3: conditional effect by safeguards
    h3 = []
    for y, (df, t, g, kind) in panels.items():
        strata = {}
        for k, lab in [(1.0, "high"), (0.0, "low")]:
            res = R.safe(R.cs, df[df["high_safeguard"] == k], y, t, g, covs, label=f"H3 {y} {lab}")
            strata[lab] = res
            if res is not None:
                R.record("H3", y, f"safeguards {lab} (median split)", res)
        if strata["high"] is not None and strata["low"] is not None:
            hi, lo = strata["high"].overall.iloc[0], strata["low"].overall.iloc[0]
            diff = hi["att"] - lo["att"]
            se = float(np.hypot(hi["se"], lo["se"]))
            p = float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(diff / se))))
            h3.append(R.record("H3", y, "difference high - low", att=diff, se=se,
                               ci_low=diff - 1.96 * se, ci_high=diff + 1.96 * se, p_value=p))
        tab, fit = R.safe(twfe.interaction, df, y, UNIT, t, g, "safeguard", label=f"H3 TWFE {y}") or (None, None)
        if tab is not None:
            wb = wildboot.wild_from_fit(fit, "_DxS", n_boot=s["wild_bootstrap"]["n_boot"],
                                        weights=s["wild_bootstrap"]["weights"], seed=s["seed"])
            r = tab.loc["D_x_safeguard"]
            R.record("H3 (TWFE comparison)", y, "D x safeguard (continuous, centered)", att=r["coef"], se=r["se"],
                     ci_low=r["ci_low"], ci_high=r["ci_high"], p_value=r["p_value"], p_wild=wb["p_wild"])
    if h3:
        adj = multipletests([r["p_value"] for r in h3], method="holm")[1]
        for r, p in zip(h3, adj):
            r["p_adjusted"], r["adjustment"] = p, "holm (H3)"

    # H4 (exploratory): system design
    feat = s["design"]["feature"]
    h4 = []
    for y, (df, t, g, kind) in panels.items():
        if feat not in df.columns or df[feat].notna().sum() == 0:
            R.notes.append(f"H4: {feat} not coded")
            break
        for k, lab in [(1.0, "mandatory biometric authentication"), (0.0, "non-biometric alternatives allowed")]:
            sub = df[(df[feat] == k) | df["rollout_year"].isna()]  # never-adopters remain as controls
            res = R.safe(R.cs, sub, y, t, g, covs, label=f"H4 {y} {lab}")
            if res is not None:
                h4.append(R.record("H4 (exploratory)", y, lab, res))
    if h4:
        adj = multipletests([r["p_value"] for r in h4], method="fdr_bh")[1]
        for r, p in zip(h4, adj):
            r["p_adjusted"], r["adjustment"] = p, "BH (exploratory)"

    # Robustness for H1
    rb = s["robustness"]
    for y, (df, t, g, kind) in panels.items():
        def rec(spec, res):
            if res is not None:
                R.record("H1 robustness", y, spec, res)
        if rb["never_treated_controls"]:
            rec("never-treated controls", R.safe(R.cs, df, y, t, g, covs, control_group="nevertreated", label=f"{y} never"))
        if rb["unconditional"]:
            rec("unconditional (no covariates)", R.safe(R.cs, df, y, t, g, None, label=f"{y} uncond"))
        if rb["extended_covariates"]:
            rec("extended covariates (+ SP spending)", R.safe(R.cs, df, y, t, g, est["covariates_extended"], label=f"{y} ext"))
        if rb["alt_lag"]:
            lags = [1] if kind == "annual" else [0, 2]
            for lag in lags:
                d2 = recohort(df, s, kind, lag)
                rec(f"rollout lag {lag}", R.safe(R.cs, d2, y, t, g, covs, label=f"{y} lag{lag}"))
        if rb["alt_rollout_date"] and "rollout_year_alt" in df.columns:
            d2 = recohort(df, s, kind, col="rollout_year_alt")
            rec("alternative rollout date (legal)", R.safe(R.cs, d2, y, t, g, covs, label=f"{y} altdate"))
        if rb.get("interpolate_sdg") and kind == "annual":
            d2 = interpolate_inside(df, y, t)
            rec("linear interpolation within observed years", R.safe(R.cs, d2, y, t, g, covs, label=f"{y} interp"))
        if rb["pre_covid_window"] and kind == "annual":
            rec(f"years <= {rb['pre_covid_window']}", R.safe(R.cs, df[df[t] <= rb["pre_covid_window"]], y, t, g, covs, label=f"{y} precovid"))
        if rb["exclude_donor_financed"] and "donor_financed" in df.columns:
            rec("exclude donor-financed rollouts", R.safe(R.cs, df[df["donor_financed"] != 1], y, t, g, covs, label=f"{y} donor"))
        if rb["balanced_event_study"]:
            be = a["balance_e"] if kind == "annual" else w["balance_e"]
            res = R.safe(R.cs, df, y, t, g, covs, balance_e=be, label=f"{y} balanced")
            if res is not None:
                R.write(res.dynamic, f"H1_{y}_event_study_balanced")
        if rb["leave_one_region_out"] and "region" in df.columns:
            for reg in sorted(df["region"].dropna().unique()):
                rec(f"leave out region {reg}", R.safe(R.cs, df[df["region"] != reg], y, t, g, covs, label=f"{y} -{reg}"))
        if rb["tercile_split"]:
            sg = df.drop_duplicates(UNIT)[[UNIT, "safeguard"]]
            q = sg["safeguard"].quantile([1 / 3, 2 / 3]).to_numpy()
            for lab, m in [("top tercile", df["safeguard"] > q[1]), ("bottom tercile", df["safeguard"] <= q[0])]:
                res = R.safe(R.cs, df[m], y, t, g, covs, label=f"{y} H3 {lab}")
                if res is not None:
                    R.record("H3 robustness", y, f"safeguards {lab}", res)

        # Comparison estimators
        if "sun_abraham" in rb["comparisons"]:
            sa = R.safe(sunab.sun_abraham, df, y, UNIT, t, g, control="never", label=f"{y} SA")
            if sa is not None:
                R.write(sa, f"compare_{y}_sun_abraham")
        if "did_m" in rb["comparisons"]:
            dm = R.safe(dcdh.did_m, df, y, UNIT, t, g, n_boot=R.n_boot, seed=s["seed"], label=f"{y} DID_M")
            if dm is not None:
                r = dm[0].iloc[0]
                R.record("H1 comparison", y, "DID_M (instantaneous, unconditional)", att=r["att"], se=r["se"],
                         ci_low=r["ci_low"], ci_high=r["ci_high"])
        if "twfe_static" in rb["comparisons"]:
            st = R.safe(twfe.static, df, y, UNIT, t, g, label=f"{y} TWFE")
            if st is not None:
                r = st[0].loc["D"]
                R.record("H1 comparison", y, "TWFE static (biased under heterogeneity)", att=r["coef"], se=r["se"],
                         ci_low=r["ci_low"], ci_high=r["ci_high"], p_value=r["p_value"])
        if "twfe_event_study" in rb["comparisons"]:
            es = R.safe(twfe.event_study, df, y, UNIT, t, g, window=tuple(a["event_window"]) if kind == "annual" else (-2, 2), label=f"{y} TWFE ES")
            if es is not None:
                R.write(es[0], f"compare_{y}_twfe_event_study")
        if "twfe_weights" in rb["comparisons"]:
            tw = R.safe(diagnostics.twfe_weights, df, UNIT, t, g, y=y, label=f"{y} weights")
            if tw is not None:
                R.write(tw[0], f"diagnostic_{y}_twfe_weights")
                R.notes.append(f"{y}: TWFE weights: {tw[1]['n_negative']} of {tw[1]['n_cells']} cells negative "
                               f"(sum {tw[1]['sum_negative']:.3f})")

    # Placebo outcomes (annual)
    for y in out["placebo"]:
        if y in cy.columns:
            res = R.safe(R.cs, cy, y, "year", "cohort_annual", covs, label=f"placebo {y}")
            if res is not None:
                R.record("Placebo", y, "main specification", res)

    results = pd.DataFrame(R.rows)
    R.write(results, "results_overall")
    lines = [f"# Results summary [{label}]", "",
             "Headline estimand: Callaway-Sant'Anna overall ATT (group aggregation), percentage points.",
             f"Bootstrap replications: {R.n_boot}. Read docs/analysis_plan.md before interpreting.", ""]
    cols = [c for c in ["analysis", "outcome", "spec", "att", "se", "ci_low", "ci_high", "p_value",
                        "p_adjusted", "p_wild", "pretrend_p", "n_units"] if c in results.columns]
    lines.append(results[cols].to_markdown(index=False, floatfmt=".3f") if _has_tabulate()
                 else results[cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    lines += ["", "## Notes", ""] + [f"- {n}" for n in R.notes]
    (config.OUTPUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:4]))
    print(f"{len(results)} result rows; {len(R.notes)} notes -> output/summary.md")
    return results


def _has_tabulate():
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--synthetic", action="store_true", help="run on synthetic data")
    ap.add_argument("--n-boot", type=int, default=None, help="override bootstrap replications")
    args = ap.parse_args()
    run(synthetic=args.synthetic, n_boot=args.n_boot)


if __name__ == "__main__":
    main()
