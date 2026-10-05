"""Callaway and Sant'Anna (2021) group-time average treatment effects.

Scope
-----
Staggered adoption of an absorbing binary treatment (digital ID rollout), unit = country.

- Control group: ``"notyettreated"`` (default, as in the proposal) or ``"nevertreated"``.
- Base period: ``"varying"`` (default of the R ``did`` package: pre-period cells are
  short differences t-1 -> t) or ``"universal"`` (every cell is relative to g-1; use this
  for event-study plots that feed Rambachan-Roth sensitivity analysis).
- Estimation: unconditional difference in mean changes, or the outcome-regression (OR)
  estimator of Sant'Anna and Zhao (2020) with time-invariant baseline covariates.
- Unbalanced panels: each ATT(g,t) uses the units observed at both t and the base period.
  This matters for SDG 1.3.1, which is reported irregularly.
- Inference: nonparametric cluster bootstrap (countries resampled with replacement), which
  also propagates the estimation error of the aggregation weights. Standard errors use the
  interquartile-range rule of the R ``did`` package; event-study bands are simultaneous
  (sup-t) bands.

Periods are the sorted distinct values of ``time``. With Findex waves (2014, 2017, 2021,
2024) the event time is therefore measured in waves, not years. A cohort must be one of the
periods (map rollout years to waves with :func:`idsp.treatment.wave_cohort` first), or lie
after the last period (treated after the sample ends: never treated within the window).
Units whose cohort is at or before the first period have no pre-period and are dropped
("always treated"); their number is reported.

References
----------
Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time
periods. Journal of Econometrics, 225(2), 200-230.
Sant'Anna, P. H. C., & Zhao, J. (2020). Doubly robust difference-in-differences estimators.
Journal of Econometrics, 219(1), 101-122.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

NEVER = np.iinfo(np.int64).max // 2  # cohort index for never-treated units


@dataclass
class CSResult:
    attgt: pd.DataFrame
    dynamic: pd.DataFrame
    group: pd.DataFrame
    calendar: pd.DataFrame
    overall: pd.DataFrame
    info: dict
    boot_dynamic: np.ndarray | None = field(default=None, repr=False)

    def event_study_vcov(self) -> tuple[pd.Series, pd.DataFrame]:
        """Event-study estimates and their bootstrap covariance (rows with finite estimates)."""
        dyn = self.dynamic.dropna(subset=["att"])
        idx = dyn.index.to_numpy()
        draws = self.boot_dynamic[:, idx]
        ok = ~np.isnan(draws).any(axis=1)
        cov = np.cov(draws[ok], rowvar=False)
        e = dyn["event_time"].to_numpy()
        return (pd.Series(dyn["att"].to_numpy(), index=e, name="att"),
                pd.DataFrame(np.atleast_2d(cov), index=e, columns=e))


def _iqr_se(draws: np.ndarray) -> np.ndarray:
    """Bootstrap standard error from the interquartile range (robust to outlying draws)."""
    q75 = np.nanquantile(draws, 0.75, axis=0)
    q25 = np.nanquantile(draws, 0.25, axis=0)
    return (q75 - q25) / (stats.norm.ppf(0.75) - stats.norm.ppf(0.25))


class _Design:
    """Wide representation of the panel and the fixed (weight-independent) cell structure."""

    def __init__(self, df, y, unit, time, cohort, covariates, control_group, base_period,
                 anticipation, min_treated, min_control):
        d = df[[unit, time, y, cohort] + list(covariates)].copy()
        if d.duplicated([unit, time]).any():
            raise ValueError("Duplicate (unit, time) rows.")
        self.periods = np.sort(d[time].unique())
        T = len(self.periods)
        if T < 2:
            raise ValueError("Need at least two periods.")
        coh = d.groupby(unit)[cohort].agg(["first", "nunique"])
        if (coh["nunique"] > 1).any():
            raise ValueError("Cohort must be constant within unit.")
        units = coh.index.to_numpy()
        gval = coh["first"].astype(float).to_numpy()

        gidx = np.full(len(units), NEVER, dtype=np.int64)
        pos = {p: i for i, p in enumerate(self.periods)}
        finite = np.isfinite(gval) & (gval > 0)
        for i in np.where(finite)[0]:
            g = gval[i]
            if g > self.periods[-1]:
                continue  # treated after the window: never treated within it
            if g < self.periods[0]:
                gidx[i] = -1  # treated before the window: always treated
                continue
            if g not in pos:
                raise ValueError(f"Cohort {g} of unit {units[i]} is not one of the periods; "
                                 "map rollout years to periods first.")
            gidx[i] = pos[g]
        always = gidx <= anticipation
        self.n_always_treated = int(always.sum())
        keep = ~always
        self.units = units[keep]
        self.gidx = gidx[keep]
        N = len(self.units)

        wide = d.pivot(index=unit, columns=time, values=y).reindex(index=self.units, columns=self.periods)
        self.Y = wide.to_numpy(dtype=float)
        self.X = None
        if covariates:
            xc = d.groupby(unit)[list(covariates)].agg(["first", "nunique"])
            for c in covariates:
                if (xc[(c, "nunique")] > 1).any():
                    raise ValueError(f"Covariate {c} varies within unit; use baseline values.")
            X = np.column_stack([xc[(c, "first")].reindex(self.units).to_numpy(float) for c in covariates])
            if np.isnan(X).any():
                raise ValueError("Missing covariate values; impute or drop units before estimation.")
            self.X = np.column_stack([np.ones(N), X])

        self.cohort_idx = np.unique(self.gidx[self.gidx != NEVER])
        self.cohort_member = np.vstack([(self.gidx == g).astype(float) for g in self.cohort_idx]) \
            if len(self.cohort_idx) else np.zeros((0, N))
        self.n_never = int((self.gidx == NEVER).sum())

        cells, tr_rows, ct_rows, dy_rows = [], [], [], []
        for k, g in enumerate(self.cohort_idx):
            for t in range(T):
                if base_period == "varying":
                    b = t - 1 if t < g - anticipation else g - 1 - anticipation
                    if b < 0:
                        continue
                elif base_period == "universal":
                    b = g - 1 - anticipation
                    if t == b:
                        continue
                else:
                    raise ValueError("base_period must be 'varying' or 'universal'.")
                dy = self.Y[:, t] - self.Y[:, b]
                obs = np.isfinite(dy)
                tr = (self.gidx == g) & obs
                if control_group == "notyettreated":
                    ct = (self.gidx > max(t, b) + anticipation) & (self.gidx != g) & obs
                elif control_group == "nevertreated":
                    ct = (self.gidx == NEVER) & obs
                else:
                    raise ValueError("control_group must be 'notyettreated' or 'nevertreated'.")
                if tr.sum() < min_treated or ct.sum() < min_control:
                    continue
                cells.append((k, g, t, b))
                tr_rows.append(tr.astype(float))
                ct_rows.append(ct.astype(float))
                dy_rows.append(np.where(obs, dy, 0.0))
        if not cells:
            raise ValueError("No estimable ATT(g,t) cells.")
        self.cells = np.array(cells, dtype=np.int64)  # (cohort_k, g, t, b)
        self.TR = np.vstack(tr_rows)
        self.CT = np.vstack(ct_rows)
        self.DY = np.vstack(dy_rows)
        self.event_time = self.cells[:, 2] - self.cells[:, 1]
        self.post = self.cells[:, 2] >= self.cells[:, 1]

    def att(self, W: np.ndarray) -> np.ndarray:
        """ATT(g,t) for each cell under unit weights W (N,) or (N, B). Returns (cells,) or (cells, B)."""
        with np.errstate(invalid="ignore", divide="ignore"):
            if self.X is None:
                mt = ((self.TR * self.DY) @ W) / (self.TR @ W)
                mc = ((self.CT * self.DY) @ W) / (self.CT @ W)
                out = mt - mc
            else:
                out = self._att_or(W)
        return out

    def _att_or(self, W):
        """Outcome-regression ATT for all weight vectors at once (batched weighted least squares)."""
        single = W.ndim == 1
        Wm = W[:, None] if single else W
        B = Wm.shape[1]
        X = self.X
        k = X.shape[1]
        out = np.full((len(self.cells), B), np.nan)
        for c in range(len(self.cells)):
            tr, ct, dy = self.TR[c] > 0, self.CT[c] > 0, self.DY[c]
            Xc, yc, Wc = X[ct], dy[ct], Wm[ct]
            XtWX = np.einsum("ik,il,ib->bkl", Xc, Xc, Wc)
            XtWy = np.einsum("ik,i,ib->bk", Xc, yc, Wc)
            ok = (Wc > 0).sum(axis=0) > k
            beta = (np.linalg.pinv(XtWX) @ XtWy[..., None])[..., 0]  # (B, k)
            Wt = Wm[tr]
            resid = dy[tr][:, None] - X[tr] @ beta.T  # (n_treated, B)
            den = Wt.sum(axis=0)
            with np.errstate(invalid="ignore", divide="ignore"):
                out[c] = np.where(ok & (den > 0), (Wt * resid).sum(axis=0) / den, np.nan)
        return out[:, 0] if single else out


def _aggregate(des: _Design, att: np.ndarray, W: np.ndarray, balance_e: int | None):
    """Aggregations of ATT(g,t). att: (cells, B); W: (N, B). Returns dict of arrays (k, B)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # empty bootstrap cells give NaN by design
        return _aggregate_impl(des, att, W, balance_e)


def _aggregate_impl(des, att, W, balance_e):
    pg_all = des.cohort_member @ W  # (cohorts, B)
    pg = pg_all[des.cells[:, 0]]  # (cells, B)
    valid = np.isfinite(att)
    a0 = np.where(valid, att, 0.0)
    pv = np.where(valid, pg, 0.0)
    T = len(des.periods)

    def wavg(mask):
        num = (pv[mask] * a0[mask]).sum(axis=0)
        den = pv[mask].sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / den, np.nan)

    cohort_ok = np.ones(len(des.cohort_idx), dtype=bool)
    if balance_e is not None:
        cohort_ok = des.cohort_idx + balance_e <= T - 1
    in_bal = cohort_ok[des.cells[:, 0]]

    e_vals = np.unique(des.event_time)
    dyn = np.vstack([wavg((des.event_time == e) & in_bal) for e in e_vals])

    grp = []
    for k in range(len(des.cohort_idx)):
        m = (des.cells[:, 0] == k) & des.post
        with np.errstate(invalid="ignore"):
            cnt = valid[m].sum(axis=0)
            grp.append(np.where(cnt > 0, a0[m].sum(axis=0) / np.maximum(cnt, 1), np.nan))
    grp = np.vstack(grp) if grp else np.zeros((0, att.shape[1]))
    gvalid = np.isfinite(grp)
    gw = np.where(gvalid, pg_all, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        overall_group = np.where(gw.sum(0) > 0, (gw * np.where(gvalid, grp, 0)).sum(0) / gw.sum(0), np.nan)

    t_vals = np.unique(des.cells[des.post, 2])
    cal = np.vstack([wavg((des.cells[:, 2] == t) & des.post) for t in t_vals])
    overall_cal = np.nanmean(np.where(np.isfinite(cal), cal, np.nan), axis=0) if len(t_vals) else np.nan

    overall_simple = wavg(des.post)
    post_e = e_vals >= 0
    overall_dyn = np.nanmean(dyn[post_e], axis=0) if post_e.any() else np.nan

    return dict(e_vals=e_vals, dynamic=dyn, group=grp, t_vals=t_vals, calendar=cal,
                overall=np.vstack([overall_group, overall_simple, overall_dyn, overall_cal]))


def att_gt(df: pd.DataFrame, y: str, unit: str, time: str, cohort: str,
           covariates: list[str] | None = None, control_group: str = "notyettreated",
           base_period: str = "varying", anticipation: int = 0, balance_e: int | None = None,
           n_boot: int = 999, cluster: str | None = None, alpha: float = 0.05, seed: int = 20261004,
           min_treated: int = 1, min_control: int = 2) -> CSResult:
    """Estimate ATT(g,t) and its aggregations.

    Parameters
    ----------
    df : long panel with one row per (unit, time). Missing outcomes allowed.
    cohort : first treated period of the unit; NaN, 0 or inf for never treated.
    covariates : time-invariant baseline covariates for the outcome-regression estimator.
    balance_e : if set, the event study uses only cohorts observed for event times 0..balance_e.
    cluster : optional coarser cluster variable (constant within unit) for the bootstrap.
    """
    covariates = list(covariates or [])
    des = _Design(df, y, unit, time, cohort, covariates, control_group, base_period,
                  anticipation, min_treated, min_control)
    N = len(des.units)

    W0 = np.ones((N, 1))
    att0 = des.att(W0)
    agg0 = _aggregate(des, att0, W0, balance_e)

    rng = np.random.default_rng(seed)
    if cluster is None:
        cl = np.arange(N)
    else:
        cmap = df.groupby(unit)[cluster].first().reindex(des.units)
        cl = pd.factorize(cmap)[0]
    n_cl = cl.max() + 1
    draws = rng.multinomial(n_cl, np.full(n_cl, 1.0 / n_cl), size=n_boot).T  # (n_cl, B)
    Wb = draws[cl].astype(float)  # (N, B)
    attb = des.att(Wb)
    aggb = _aggregate(des, attb, Wb, balance_e)

    z = stats.norm.ppf(1 - alpha / 2)

    def table(est, boot, extra: dict, uniform=False):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return _table(est, boot, extra, uniform)

    def _table(est, boot, extra, uniform):
        se = _iqr_se(boot.T) if boot.size else np.array([])
        out = pd.DataFrame(extra)
        out["att"] = est
        out["se"] = se
        crit = z
        if uniform and len(est):
            ok = np.isfinite(est) & (se > 0)
            if ok.any():
                tstat = np.abs(boot[ok] - est[ok, None]) / se[ok, None]
                crit = float(np.nanquantile(np.nanmax(tstat, axis=0), 1 - alpha))
        out["ci_low"] = est - crit * se
        out["ci_high"] = est + crit * se
        if uniform:
            out["crit_value"] = crit
        return out

    periods = des.periods
    cells = des.cells
    attgt = table(att0[:, 0], attb, {
        "cohort": periods[cells[:, 1]], "time": periods[cells[:, 2]],
        "base_time": periods[cells[:, 3]], "event_time": des.event_time,
        "n_treated": des.TR.sum(1).astype(int), "n_control": des.CT.sum(1).astype(int)})
    dynamic = table(agg0["dynamic"][:, 0], aggb["dynamic"], {"event_time": agg0["e_vals"]}, uniform=True)
    group = table(agg0["group"][:, 0], aggb["group"], {"cohort": periods[des.cohort_idx]})
    calendar = table(agg0["calendar"][:, 0], aggb["calendar"], {"time": periods[agg0["t_vals"]]})
    overall = table(agg0["overall"][:, 0], aggb["overall"],
                    {"aggregation": ["group (headline)", "simple", "dynamic (mean of post)", "calendar"]})
    overall["p_value"] = 2 * (1 - stats.norm.cdf(np.abs(overall["att"] / overall["se"])))

    info = dict(n_units=N, n_always_treated_dropped=des.n_always_treated, n_never_treated=des.n_never,
                n_cohorts=len(des.cohort_idx), periods=list(periods), control_group=control_group,
                base_period=base_period, anticipation=anticipation, covariates=covariates,
                n_boot=n_boot, alpha=alpha, seed=seed, balance_e=balance_e,
                cohort_sizes={str(periods[g]): int((des.gidx == g).sum()) for g in des.cohort_idx})
    return CSResult(attgt=attgt, dynamic=dynamic, group=group, calendar=calendar, overall=overall,
                    info=info, boot_dynamic=aggb["dynamic"].T)
