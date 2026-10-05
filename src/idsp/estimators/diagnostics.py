"""Diagnostics for staggered designs.

- twfe_weights: weights that the static TWFE coefficient attaches to each treated
  (cohort, period) cell (de Chaisemartin & D'Haultfoeuille, 2020, Theorem 1). Negative weights
  mean that TWFE can have the wrong sign even if every cell effect is positive.
- pretrend_wald: joint Wald test that all pre-period event-study estimates are zero, using the
  bootstrap covariance. Failing to reject is not evidence of parallel trends: pre-tests have low
  power and conditioning on them distorts inference (Roth, 2022). Report it together with the
  Rambachan-Roth sensitivity analysis (r/honestdid.R).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ._common import NEVER, add_period_index, ols_fe


def twfe_weights(df, unit, time, cohort, y=None):
    d, periods = add_period_index(df, unit, time, cohort)
    d = d[d["_g"] != -1].copy()
    if y is not None:
        d = d.dropna(subset=[y])
    # Residualize D on unit and time fixed effects.
    fit = ols_fe(d.assign(_y=d["_D"]), "_y", [], unit, time)
    resid = fit.y - fit.X @ np.linalg.pinv(fit.X) @ fit.y
    d = d.reset_index(drop=True)
    d["_eps"] = resid
    tr = d[d["_D"] == 1]
    w = tr.groupby(["_g", "_t"])["_eps"].sum() / tr["_eps"].sum()
    cells = w.reset_index().rename(columns={"_eps": "weight"})
    cells["cohort"] = periods[cells["_g"]]
    cells["time"] = periods[cells["_t"]]
    cells["event_time"] = cells["_t"] - cells["_g"]
    cells = cells[["cohort", "time", "event_time", "weight"]]
    summary = dict(n_cells=len(cells), n_negative=int((cells["weight"] < 0).sum()),
                   sum_negative=float(cells.loc[cells["weight"] < 0, "weight"].sum()))
    return cells, summary


def pretrend_wald(cs_result):
    """Joint test that pre-period event-study estimates equal zero (CS result)."""
    est, cov = cs_result.event_study_vcov()
    pre = est.index < 0
    if pre.sum() == 0:
        return dict(stat=np.nan, df=0, p_value=np.nan, note="no pre-periods")
    b = est[pre].to_numpy()
    V = cov.loc[pre, pre].to_numpy()
    stat = float(b @ np.linalg.pinv(V) @ b)
    k = int(pre.sum())
    return dict(stat=stat, df=k, p_value=float(1 - stats.chi2.cdf(stat, k)))
