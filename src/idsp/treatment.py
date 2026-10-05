"""Treatment timing: from hand-coded rollout years to cohorts and treatment indicators.

Annual outcomes (SDG 1.3.1): a country is treated from ``rollout_year + lag`` onward.
Findex waves: a country is treated at the first wave w with ``rollout_year + lag_years <= w``.
The default lag of one year avoids counting a country as treated in a survey wave fielded in
the same calendar year as the start of enrolment. Both lags are analysis choices recorded in
config/settings.yaml and docs/analysis_plan.md; change them only through docs/deviations.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def annual_cohort(rollout_year, lag: int = 0):
    """First treated year for annual outcomes (NaN = never treated)."""
    r = pd.to_numeric(pd.Series(rollout_year), errors="coerce")
    return (r + lag).to_numpy()


def wave_cohort(rollout_year, waves, lag_years: int = 1) -> float:
    """First survey wave at which the country counts as treated (NaN = never within the waves).

    A return value equal to the first wave means the country was already treated at baseline
    (always treated): it has no pre-period and is dropped by the estimators.
    """
    if rollout_year is None or not np.isfinite(rollout_year):
        return np.nan
    for w in sorted(waves):
        if rollout_year + lag_years <= w:
            return float(w)
    return np.nan


def cohort_table(countries: pd.DataFrame, cohort_col: str, first_period, last_period) -> pd.DataFrame:
    """Number of countries per adoption cohort, with always- and never-treated rows."""
    g = countries[cohort_col]
    label = np.where(g.isna() | (g > last_period), "never treated in window",
                     np.where(g <= first_period, "always treated (dropped)", g.astype("Int64").astype(str)))
    return (pd.Series(label, name="cohort").value_counts().rename_axis("cohort")
            .reset_index(name="n_countries").sort_values("cohort").reset_index(drop=True))
