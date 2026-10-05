"""Two-way fixed effects specifications, reported only for comparison.

With staggered adoption and effects that vary over time, the static TWFE coefficient is a
weighted average of group-time effects with possibly negative weights (Goodman-Bacon, 2021;
de Chaisemartin & D'Haultfoeuille, 2020). The proposal therefore uses Callaway-Sant'Anna as the
main estimator. TWFE is kept for (i) comparison with earlier literature and (ii) the H3
interaction specification written in the proposal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ._common import NEVER, add_period_index, ols_fe


def _table(fit, alpha=0.05):
    z = stats.norm.ppf(1 - alpha / 2)
    se = fit.se
    out = pd.DataFrame({"coef": fit.params, "se": se})
    out["ci_low"] = out["coef"] - z * out["se"]
    out["ci_high"] = out["coef"] + z * out["se"]
    out["p_value"] = 2 * (1 - stats.norm.cdf(np.abs(out["coef"] / out["se"])))
    out.attrs.update(nobs=fit.nobs, n_clusters=fit.n_clusters)
    return out


def static(df, y, unit, time, cohort, cluster=None, drop_always_treated=True, alpha=0.05):
    """Y_it = a_i + l_t + beta * D_it + e_it."""
    d, _ = add_period_index(df, unit, time, cohort)
    if drop_always_treated:
        d = d[d["_g"] != -1]
    fit = ols_fe(d, y, ["_D"], unit, time, cluster)
    return _table(fit, alpha).rename(index={"_D": "D"}), fit


def interaction(df, y, unit, time, cohort, moderator, cluster=None, drop_always_treated=True,
                center=True, alpha=0.05):
    """H3 specification of the proposal: Y_it = a_i + l_t + beta*D_it + gamma*(D_it x S_i) + e_it.

    The moderator S_i must be time-invariant (measured before rollout); its main effect is
    absorbed by the unit fixed effects. Centering makes beta the effect at the mean of S.
    """
    d, _ = add_period_index(df, unit, time, cohort)
    if drop_always_treated:
        d = d[d["_g"] != -1]
    if d.groupby(unit)[moderator].nunique().max() > 1:
        raise ValueError("Moderator must be time-invariant (baseline value).")
    s = d[moderator] - (d.drop_duplicates(unit)[moderator].mean() if center else 0.0)
    d["_DxS"] = d["_D"] * s
    fit = ols_fe(d, y, ["_D", "_DxS"], unit, time, cluster)
    return _table(fit, alpha).rename(index={"_D": "D", "_DxS": "D_x_safeguard"}), fit


def event_study(df, y, unit, time, cohort, window=(-3, 3), cluster=None, drop_always_treated=True,
                alpha=0.05):
    """TWFE event study with relative-period dummies (reference e = -1, endpoints binned)."""
    lo, hi = window
    d, _ = add_period_index(df, unit, time, cohort)
    if drop_always_treated:
        d = d[d["_g"] != -1]
    e = d["_e"].clip(lower=lo, upper=hi)
    names = []
    for k in range(lo, hi + 1):
        if k == -1:
            continue
        nm = f"e_{k}".replace("-", "m")
        d[nm] = ((e == k) & (d["_g"] != NEVER)).astype(float)
        if d[nm].sum() > 0:
            names.append(nm)
    fit = ols_fe(d, y, names, unit, time, cluster)
    out = _table(fit, alpha)
    out.insert(0, "event_time", [int(n[2:].replace("m", "-")) for n in names])
    return out.reset_index(drop=True), fit
