"""Estimators for staggered adoption designs.

- cs: Callaway and Sant'Anna (2021) group-time ATTs and aggregations (main estimator).
- sunab: Sun and Abraham (2021) interaction-weighted event study (comparison).
- dcdh: de Chaisemartin and D'Haultfoeuille (2020) DID_M for absorbing binary treatment (comparison).
- twfe: two-way fixed effects with cluster-robust standard errors (comparison and H3 interaction).
- diagnostics: TWFE negative-weight diagnostic and pre-trend Wald test.
- wildboot: wild cluster restricted bootstrap for OLS coefficients.
"""
