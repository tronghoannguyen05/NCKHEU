"""Sun and Abraham (2021) interaction-weighted (IW) event-study estimator.

Cohort x relative-period interactions are estimated in one TWFE regression with a clean
control cohort (never treated, or the last-treated cohort with periods from its adoption
onward removed). Each event-time effect is the average of the cohort-specific coefficients
weighted by the cohorts' shares among units observed at that relative period. Standard errors
treat the shares as fixed (delta method on the cluster-robust covariance).

Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with
heterogeneous treatment effects. Journal of Econometrics, 225(2), 175-199.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ._common import NEVER, add_period_index, ols_fe


def sun_abraham(df, y, unit, time, cohort, control="never", cluster=None, alpha=0.05):
    d, periods = add_period_index(df, unit, time, cohort)
    d = d[d["_g"] != -1].copy()
    d = d.dropna(subset=[y])
    if control == "never":
        if (d["_g"] == NEVER).sum() == 0:
            raise ValueError("No never-treated units; use control='last'.")
        ctrl = d["_g"] == NEVER
    elif control == "last":
        last = d.loc[d["_g"] != NEVER, "_g"].max()
        d = d[(d["_t"] < last) | (d["_g"] == NEVER)]
        ctrl = d["_g"].isin([last, NEVER])
    else:
        raise ValueError("control must be 'never' or 'last'.")
    d["_ctrl"] = ctrl.to_numpy()
    names, keys = [], []
    new_cols = {}
    for (g, e), sub in d[~d["_ctrl"]].groupby(["_g", "_e"]):
        if e == -1:
            continue
        nm = f"g{g}_e{int(e)}".replace("-", "m")
        new_cols[nm] = ((d["_g"] == g) & (d["_e"] == e)).astype(float)
        names.append(nm)
        keys.append((g, int(e), len(sub)))
    d = pd.concat([d, pd.DataFrame(new_cols, index=d.index)], axis=1)
    fit = ols_fe(d, y, names, unit, time, cluster)
    k = pd.DataFrame(keys, columns=["g", "e", "n"], index=names)
    z = stats.norm.ppf(1 - alpha / 2)
    rows = []
    for e, sub in k.groupby("e"):
        w = (sub["n"] / sub["n"].sum()).to_numpy()
        b = fit.params[sub.index].to_numpy()
        V = fit.vcov.loc[sub.index, sub.index].to_numpy()
        est = float(w @ b)
        se = float(np.sqrt(w @ V @ w))
        rows.append(dict(event_time=e, att=est, se=se, ci_low=est - z * se, ci_high=est + z * se,
                         n_cohorts=len(sub)))
    out = pd.DataFrame(rows)
    out.attrs.update(nobs=fit.nobs, n_clusters=fit.n_clusters, control=control,
                     periods=list(periods))
    return out
