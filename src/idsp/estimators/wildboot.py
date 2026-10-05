"""Wild cluster restricted (WCR) bootstrap for one OLS coefficient.

Used when few clusters carry the identifying variation (small subgroups, H3 and H4 splits).
The null H0: beta_k = 0 is imposed, residuals of the restricted model are multiplied by
cluster-level weights (Rademacher or Webb six-point), and the bootstrap t-statistics use the
CRV1 standard error (Cameron, Gelbach & Miller, 2008; Webb, 2023).

Implementation note: with A = (X'X)^+ X', the bootstrap coefficient and the cluster scores are
linear in the weights, so all replications are computed with matrix products.
"""

from __future__ import annotations

import numpy as np

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def wild_cluster_p(X, y, clusters, k, n_boot=9999, weights="webb", seed=20261004, chunk=1000,
                   k_eff=None):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    cl = np.asarray(clusters)
    n, K = X.shape
    G = cl.max() + 1
    k_eff = K if k_eff is None else k_eff
    c = G / (G - 1) * (n - 1) / (n - k_eff)

    A = np.linalg.pinv(X)  # (K, n)
    Ak = A[k]
    beta = A @ y
    u = y - X @ beta
    s = np.zeros(G); np.add.at(s, cl, Ak * u)
    se = np.sqrt(c * (s ** 2).sum())
    t_obs = beta[k] / se

    Xr = np.delete(X, k, axis=1)
    br = np.linalg.pinv(Xr) @ y
    ur = y - Xr @ br

    # Per-cluster score matrix R (G, n) such that S = R @ (ur * v) gives cluster scores.
    Q = np.zeros((G, n)); Q[cl, np.arange(n)] = Ak
    R = Q - (Q @ X) @ A
    a = np.zeros(G); np.add.at(a, cl, Ak * ur)

    rng = np.random.default_rng(seed)
    t_boot = []
    for start in range(0, n_boot, chunk):
        b = min(chunk, n_boot - start)
        if weights == "rademacher":
            v = rng.choice([-1.0, 1.0], size=(G, b))
        elif weights == "webb":
            v = rng.choice(WEBB, size=(G, b))
        else:
            raise ValueError("weights must be 'rademacher' or 'webb'.")
        beta_star = a @ v
        S = R @ (ur[:, None] * v[cl])
        se_star = np.sqrt(c * (S ** 2).sum(axis=0))
        t_boot.append(beta_star / se_star)
    t_boot = np.concatenate(t_boot)
    p = float(np.mean(np.abs(t_boot) >= abs(t_obs)))
    return dict(coef=float(beta[k]), se_crv1=float(se), t=float(t_obs), p_wild=p, n_clusters=int(G),
                n_boot=n_boot, weights=weights)


def wild_from_fit(fit, name, **kw):
    """Wild bootstrap p-value for a regressor of an :class:`OLSFit` from ``ols_fe``."""
    k = fit.columns.index(name)
    return wild_cluster_p(fit.X, fit.y, fit.clusters, k, k_eff=fit.k_eff, **kw)
