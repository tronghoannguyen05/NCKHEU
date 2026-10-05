"""Synthetic country-year and country-wave panels with known treatment effects.

Used to test the estimators and to run the full pipeline before real data are assembled.
Country codes start with "S" so that synthetic rows can never be mistaken for real ISO3 codes.
Every output produced from these data is labelled SYNTHETIC by the pipeline.

Data-generating process (all parameters adjustable):
- Rollout years: a share of countries adopt before the window (always treated), a share
  never adopt within it, the rest adopt in 2015-2024.
- Baseline safeguard components (data protection law year, WGI voice and accountability,
  WGI rule of law, V-Dem civil society participation) load on a latent safeguard factor s_i.
- Effect on coverage at event time e >= 0 (years since rollout):
  tau_it = (att_base + att_slope * e) * (1 + safeguard_mod * s_i).
- Findex groups: disadvantaged groups (women, poorest 40%, rural) receive a fraction
  (1 - gap_share_low) of the effect where safeguards are below the median, so gaps widen there.
- Optional covariate-specific trend and early adoption by richer countries make unconditional
  DiD biased and the covariate-adjusted estimator necessary.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .treatment import wave_cohort


def make_synthetic(n_countries=120, years=range(2014, 2025), waves=(2014, 2017, 2021, 2024),
                   share_always=0.15, share_never=0.15, att_base=3.0, att_slope=1.0,
                   safeguard_mod=0.5, gap_share_low=0.5, sdg_missing=0.4, covariate_trend=0.0,
                   noise_sd=2.0, wave_lag_years=1, seed=1):
    rng = np.random.default_rng(seed)
    years = np.array(list(years))
    n = n_countries
    iso3 = np.array([f"S{i:03d}" for i in range(n)])

    kind = rng.choice(["always", "never", "staggered"], size=n,
                      p=[share_always, share_never, 1 - share_always - share_never])
    log_gdppc = rng.normal(8.0, 1.0, n)
    # Richer countries adopt earlier when covariate_trend != 0 (selection on a trend-relevant covariate).
    order_noise = rng.normal(0, 1, n) - (0.8 * (log_gdppc - 8.0) if covariate_trend else 0.0)
    rank = pd.Series(order_noise).rank(pct=True).to_numpy()
    staggered_year = (2015 + np.floor(rank * 10)).clip(2015, 2024)
    rollout = np.where(kind == "always", rng.integers(2005, 2014, n).astype(float),
                       np.where(kind == "never", np.nan, staggered_year))

    s_latent = rng.normal(0, 1, n)
    wgi_va = 0.8 * s_latent + rng.normal(0, 0.6, n)
    wgi_rl = 0.7 * s_latent + rng.normal(0, 0.7, n)
    vdem_cspart = 1 / (1 + np.exp(-(0.9 * s_latent + rng.normal(0, 0.5, n))))
    dp_law_year = np.where(s_latent + rng.normal(0, 0.8, n) > 0,
                           rng.integers(2000, 2024, n), np.nan).astype(float)
    s_std = (s_latent - s_latent.mean()) / s_latent.std()
    biometric_mandatory = rng.binomial(1, 0.4, n)

    regions = rng.choice(["EAP", "ECA", "LAC", "MNA", "SAS", "SSA"], size=n)
    alt_shift = rng.choice([-2, -1, 0, 0, 0, 1], size=n)
    countries = pd.DataFrame({
        "iso3": iso3, "region": regions, "rollout_year": rollout, "rollout_kind": kind,
        "rollout_year_alt": np.where(np.isfinite(rollout), rollout + alt_shift, np.nan),
        "log_gdppc_2014": log_gdppc, "urban_2014": rng.uniform(20, 80, n),
        "mobile_2014": rng.uniform(40, 130, n), "conflict_2010_2014": rng.binomial(1, 0.2, n).astype(float),
        "sp_spending_2014": rng.uniform(0.5, 8, n), "donor_financed": rng.binomial(1, 0.3, n),
        "wgi_va_2014": wgi_va, "wgi_rl_2014": wgi_rl, "vdem_cspart_2014": vdem_cspart,
        "dp_law_year": dp_law_year, "biometric_auth_mandatory_benefits": biometric_mandatory,
        "safeguard_true": s_std,
    })

    alpha = rng.normal(40, 12, n)
    rows = []
    for i in range(n):
        for t in years:
            e = t - rollout[i] if np.isfinite(rollout[i]) else -np.inf
            tau = (att_base + att_slope * e) * (1 + safeguard_mod * s_std[i]) if e >= 0 else 0.0
            trend = covariate_trend * (log_gdppc[i] - 8.0) * (t - years[0])
            y = alpha[i] + 0.5 * (t - years[0]) + trend + tau + rng.normal(0, noise_sd)
            elec = 60 + 0.3 * alpha[i] + 1.5 * (t - years[0]) + rng.normal(0, noise_sd)
            agri = 40 + 0.1 * alpha[i] + rng.normal(0, noise_sd)
            rows.append((iso3[i], t, y, tau, elec, agri))
    cy = pd.DataFrame(rows, columns=["iso3", "year", "sdg131_total", "tau_sdg", "elec_access", "agri_land"])
    cy.loc[rng.random(len(cy)) < sdg_missing, "sdg131_total"] = np.nan
    cy = cy.merge(countries, on="iso3")
    cy["cohort_annual"] = cy["rollout_year"]

    low = s_std < np.median(s_std)
    rows = []
    for i in range(n):
        for w in waves:
            e = w - rollout[i] if np.isfinite(rollout[i]) else -np.inf
            tau = (att_base + att_slope * e) * (1 + safeguard_mod * s_std[i]) if e >= wave_lag_years else 0.0
            tau_dis = tau * (1 - gap_share_low) if low[i] else tau
            base = alpha[i] * 0.8 + 1.0 * (w - waves[0]) + covariate_trend * (log_gdppc[i] - 8.0) * (w - waves[0])
            eps = lambda: rng.normal(0, noise_sd)  # noqa: E731
            rec = dict(iso3=iso3[i], wave=w,
                       transfer_male=base + 2 + tau + eps(), transfer_female=base - 2 + tau_dis + eps(),
                       transfer_rich60=base + 3 + tau + eps(), transfer_poor40=base - 4 + tau_dis + eps(),
                       transfer_urban=base + 1 + tau + eps(), transfer_rural=base - 3 + tau_dis + eps(),
                       tau_total=(tau + tau_dis) / 2, tau_gap=tau - tau_dis)
            rec["transfer_total"] = (rec["transfer_male"] + rec["transfer_female"]) / 2
            rows.append(rec)
    cw = pd.DataFrame(rows).merge(countries, on="iso3")
    cw["cohort_wave"] = [wave_cohort(r, waves, wave_lag_years) for r in cw["rollout_year"]]
    return dict(countries=countries, country_year=cy, country_wave=cw)
