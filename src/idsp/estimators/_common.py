"""Shared helpers: period indexing of cohorts and fixed-effects OLS with cluster-robust variance."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

NEVER = np.iinfo(np.int64).max // 2


def cohort_index(periods: np.ndarray, cohort_values: np.ndarray) -> np.ndarray:
    """Map cohort values to positions in ``periods``.

    Returns -1 for cohorts at or before the first period (always treated), NEVER for
    never-treated (NaN, 0, inf, or after the last period). Raises if a cohort falls between
    periods, because rollout years must first be mapped to periods (e.g. Findex waves).
    """
    pos = {p: i for i, p in enumerate(periods)}
    out = np.full(len(cohort_values), NEVER, dtype=np.int64)
    for i, g in enumerate(np.asarray(cohort_values, dtype=float)):
        if not np.isfinite(g) or g <= 0 or g > periods[-1]:
            continue
        if g <= periods[0]:
            out[i] = -1
        elif g in pos:
            out[i] = pos[g]
        else:
            raise ValueError(f"Cohort {g} is not one of the periods; map rollout years to periods first.")
    return out


def add_period_index(df: pd.DataFrame, unit: str, time: str, cohort: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Add columns _t (period position), _g (cohort position), _D (treated) and _e (event time)."""
    periods = np.sort(df[time].unique())
    d = df.copy()
    d["_t"] = pd.Index(periods).get_indexer(d[time])
    g_unit = d.groupby(unit)[cohort].first()
    gmap = pd.Series(cohort_index(periods, g_unit.to_numpy()), index=g_unit.index)
    d["_g"] = d[unit].map(gmap).astype(np.int64)
    d["_D"] = ((d["_g"] != NEVER) & (d["_t"] >= d["_g"])).astype(float)
    d["_e"] = np.where(d["_g"] != NEVER, d["_t"] - d["_g"], np.nan)
    return d, periods


@dataclass
class OLSFit:
    params: pd.Series
    vcov: pd.DataFrame
    nobs: int
    n_clusters: int
    X: np.ndarray
    y: np.ndarray
    clusters: np.ndarray
    columns: list[str]
    k_eff: int

    @property
    def se(self) -> pd.Series:
        return pd.Series(np.sqrt(np.diag(self.vcov.to_numpy())), index=self.vcov.index)


def ols_fe(df: pd.DataFrame, y: str, regressors: list[str], unit: str, time: str,
           cluster: str | None = None) -> OLSFit:
    """OLS of y on regressors with unit and time fixed effects (dummy-variable form).

    Cluster-robust (CRV1) variance with small-sample factor G/(G-1) * (N-1)/(N-K). When unit
    fixed effects are nested in the clusters (the default: cluster = unit), the unit dummies are
    not counted in K, following the convention of fixest and reghdfe.
    """
    cluster = cluster or unit
    d = df.dropna(subset=[y] + regressors).reset_index(drop=True)
    U = pd.get_dummies(d[unit], drop_first=True, dtype=float)
    Tm = pd.get_dummies(d[time], prefix="t", drop_first=True, dtype=float)
    const = pd.DataFrame({"const": np.ones(len(d))}, index=d.index)
    Xdf = pd.concat([const, d[regressors].astype(float), U.add_prefix("u_"), Tm], axis=1)
    X = Xdf.to_numpy()
    yv = d[y].to_numpy(float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ yv
    u = yv - X @ beta
    cl = pd.factorize(d[cluster])[0]
    G = cl.max() + 1
    S = np.zeros((G, X.shape[1]))
    np.add.at(S, cl, X * u[:, None])
    meat = S.T @ S
    nested = (d.groupby(unit)[cluster].nunique() == 1).all()
    K = X.shape[1] - (U.shape[1] if nested else 0)
    n = len(yv)
    c = G / (G - 1) * (n - 1) / (n - K)
    V = c * XtX_inv @ meat @ XtX_inv
    k = len(regressors)
    idx = list(range(1, 1 + k))
    params = pd.Series(beta[idx], index=regressors)
    vcov = pd.DataFrame(V[np.ix_(idx, idx)], index=regressors, columns=regressors)
    return OLSFit(params=params, vcov=vcov, nobs=n, n_clusters=G, X=X, y=yv, clusters=cl,
                  columns=list(Xdf.columns), k_eff=K)
