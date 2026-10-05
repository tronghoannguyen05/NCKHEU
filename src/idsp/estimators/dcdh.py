"""de Chaisemartin and D'Haultfoeuille (2020) DID_M estimator for an absorbing binary treatment.

For each period t, units that switch into treatment between t-1 and t are compared with units
untreated in both periods; the period-specific estimates are averaged with weights equal to the
number of switchers. With an absorbing treatment there are no switchers out, so DID_M is the
instantaneous effect (event time 0). The dynamic estimator of de Chaisemartin and
D'Haultfoeuille (did_multiplegt_dyn in Stata/R) should be used for later event times; this
module provides the instantaneous version as a comparison.

de Chaisemartin, C., & D'Haultfoeuille, X. (2020). Two-way fixed effects estimators with
heterogeneous treatment effects. American Economic Review, 110(9), 2964-2996.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ._common import NEVER, add_period_index


def did_m(df, y, unit, time, cohort, n_boot=999, seed=20261004, alpha=0.05):
    d, periods = add_period_index(df, unit, time, cohort)
    d = d[d["_g"] != -1]
    units = np.sort(d[unit].unique())
    Y = d.pivot(index=unit, columns="_t", values=y).reindex(index=units, columns=range(len(periods))).to_numpy(float)
    g = d.groupby(unit)["_g"].first().reindex(units).to_numpy()
    T = len(periods)
    S_rows, C_rows, DY_rows, tt = [], [], [], []
    for t in range(1, T):
        dy = Y[:, t] - Y[:, t - 1]
        obs = np.isfinite(dy)
        S = (g == t) & obs
        C = (g > t) & obs  # untreated at t-1 and t (includes never treated)
        if S.sum() == 0 or C.sum() < 2:
            continue
        S_rows.append(S.astype(float)); C_rows.append(C.astype(float))
        DY_rows.append(np.where(obs, dy, 0.0)); tt.append(t)
    if not S_rows:
        raise ValueError("No switchers.")
    S, C, DY = np.vstack(S_rows), np.vstack(C_rows), np.vstack(DY_rows)

    def est(W):
        with np.errstate(invalid="ignore", divide="ignore"):
            ns = S @ W
            did_t = ((S * DY) @ W) / ns - ((C * DY) @ W) / (C @ W)
            num = np.nansum(np.where(ns > 0, ns * did_t, 0), axis=0)
            return num / ns.sum(axis=0), did_t

    N = len(units)
    point, did_t = est(np.ones((N, 1)))
    rng = np.random.default_rng(seed)
    Wb = rng.multinomial(N, np.full(N, 1.0 / N), size=n_boot).T.astype(float)
    boot, did_tb = est(Wb)
    se = float(np.nanstd(boot, ddof=1))
    z = stats.norm.ppf(1 - alpha / 2)
    out = pd.DataFrame({"estimate": ["DID_M (instantaneous)"], "att": [point[0]], "se": [se]})
    out["ci_low"] = out["att"] - z * se
    out["ci_high"] = out["att"] + z * se
    out["n_switchers"] = int(S.sum())
    by_t = pd.DataFrame({"time": periods[tt], "did_t": did_t[:, 0], "n_switchers": S.sum(1).astype(int),
                         "se": np.nanstd(did_tb, axis=1, ddof=1)})
    return out, by_t
