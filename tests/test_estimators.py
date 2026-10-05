import numpy as np
import pandas as pd
import pytest

from idsp.estimators import cs, dcdh, diagnostics, sunab, twfe, wildboot
from idsp.synthetic import make_synthetic


@pytest.fixture(scope="module")
def big():
    return make_synthetic(n_countries=800, sdg_missing=0.0, noise_sd=1.0, seed=3)["country_year"]


def _truth(df, a):
    t = df.groupby(["cohort_annual", "year"])["tau_sdg"].mean()
    return np.array([t[(g, y)] if y >= g else 0.0 for g, y in zip(a["cohort"], a["time"])])


def test_cs_recovers_group_time_effects(big):
    r = cs.att_gt(big, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=99)
    a = r.attgt
    err = a["att"].to_numpy() - _truth(big, a)
    assert np.abs(err[a["event_time"] >= 0]).mean() < 0.3
    assert np.abs(err[a["event_time"] < 0]).mean() < 0.3
    assert r.info["n_always_treated_dropped"] > 0


def test_cs_two_by_two_equals_simple_did():
    df = pd.DataFrame({"u": [1, 1, 2, 2, 3, 3, 4, 4], "t": [1, 2] * 4,
                       "y": [1, 4, 2, 6, 3, 3.5, 5, 5.5], "g": [2, 2, 2, 2, 0, 0, 0, 0]})
    r = cs.att_gt(df, "y", "u", "t", "g", n_boot=9, min_control=1)
    did = ((4 - 1) + (6 - 2)) / 2 - ((3.5 - 3) + (5.5 - 5)) / 2
    assert r.attgt["att"].iloc[0] == pytest.approx(did)


def test_cs_unbalanced_uses_pairwise_observed_units():
    d = make_synthetic(n_countries=600, sdg_missing=0.3, noise_sd=1.0, seed=4)["country_year"]
    r = cs.att_gt(d, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=49)
    a = r.attgt
    err = a["att"].to_numpy() - _truth(d, a)
    # Cells use different subsets of a heterogeneous cohort, so check the signed mean (bias).
    assert abs(np.nanmean(err[a["event_time"] >= 0])) < 0.3


def test_cs_outcome_regression_removes_covariate_trend_bias():
    d = make_synthetic(n_countries=800, sdg_missing=0.0, covariate_trend=0.8, noise_sd=1.0, seed=5)["country_year"]
    unc = cs.att_gt(d, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=19)
    orr = cs.att_gt(d, "sdg131_total", "iso3", "year", "cohort_annual", covariates=["log_gdppc_2014"], n_boot=19)
    post = unc.attgt["event_time"] >= 0
    bias_unc = (unc.attgt["att"] - _truth(d, unc.attgt))[post].mean()
    bias_or = (orr.attgt["att"] - _truth(d, orr.attgt))[post].mean()
    assert abs(bias_or) < 0.3 < abs(bias_unc)


def test_cs_bootstrap_and_bands(big):
    r = cs.att_gt(big, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=199)
    dyn = r.dynamic
    assert (dyn["se"] > 0).all()
    assert (dyn["crit_value"].iloc[0] >= 1.96)
    est, cov = r.event_study_vcov()
    assert cov.shape == (len(est), len(est))
    w = diagnostics.pretrend_wald(r)
    assert 0 <= w["p_value"] <= 1


def test_cs_universal_base_and_never_treated(big):
    r = cs.att_gt(big, "sdg131_total", "iso3", "year", "cohort_annual", base_period="universal",
                  control_group="nevertreated", n_boot=49)
    assert -1 not in set(r.attgt["event_time"])
    assert abs(r.overall["att"].iloc[0] - 0) > 1  # positive effects in the DGP


def test_did_m_equals_cs_instantaneous_in_balanced_panel(big):
    r = cs.att_gt(big, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=19)
    a = r.attgt[r.attgt["event_time"] == 0]
    cs_inst = (a["att"] * a["n_treated"]).sum() / a["n_treated"].sum()
    dm, _ = dcdh.did_m(big, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=19)
    assert dm["att"].iloc[0] == pytest.approx(cs_inst, rel=1e-10)


def test_sun_abraham_recovers_event_time_effects(big):
    sa = sunab.sun_abraham(big, "sdg131_total", "iso3", "year", "cohort_annual")
    r = cs.att_gt(big, "sdg131_total", "iso3", "year", "cohort_annual", n_boot=19)
    m = sa.merge(r.dynamic, on="event_time", suffixes=("_sa", "_cs"))
    post = m[(m["event_time"] >= 0) & (m["event_time"] <= 5)]
    assert np.abs(post["att_sa"] - post["att_cs"]).max() < 0.5


def test_twfe_static_unbiased_with_homogeneous_effect():
    d = make_synthetic(n_countries=600, sdg_missing=0.0, att_slope=0.0, safeguard_mod=0.0,
                       noise_sd=1.0, seed=6)["country_year"]
    st, _ = twfe.static(d, "sdg131_total", "iso3", "year", "cohort_annual")
    assert st.loc["D", "coef"] == pytest.approx(3.0, abs=0.2)


def test_twfe_weights_negative_with_dynamic_effects(big):
    cells, summary = diagnostics.twfe_weights(big, "iso3", "year", "cohort_annual")
    assert summary["n_negative"] > 0
    assert cells["weight"].sum() == pytest.approx(1.0)


def test_wild_bootstrap_size_and_power():
    rng = np.random.default_rng(0)
    G, m = 40, 10
    cl = np.repeat(np.arange(G), m)
    x = rng.normal(size=G * m) + rng.normal(size=G)[cl]
    X = np.column_stack([np.ones(G * m), x])
    y_null = rng.normal(size=G)[cl] + rng.normal(size=G * m)
    y_alt = y_null + 0.8 * x
    p_null = wildboot.wild_cluster_p(X, y_null, cl, 1, n_boot=999)["p_wild"]
    p_alt = wildboot.wild_cluster_p(X, y_alt, cl, 1, n_boot=999)["p_wild"]
    assert 0 <= p_null <= 1 and p_alt < 0.01


def test_wild_bootstrap_on_twfe_interaction(big):
    tab, fit = twfe.interaction(big, "sdg131_total", "iso3", "year", "cohort_annual", "safeguard_true")
    res = wildboot.wild_from_fit(fit, "_DxS", n_boot=499)
    assert res["coef"] == pytest.approx(tab.loc["D_x_safeguard", "coef"])
    assert res["p_wild"] < 0.05


def test_cs_matches_csdid_package():
    csdid = pytest.importorskip("csdid.att_gt")
    d = make_synthetic(n_countries=150, sdg_missing=0.0, seed=8)["country_year"].copy()
    d["g"] = d["cohort_annual"].fillna(0)
    d["id"] = pd.factorize(d["iso3"])[0] + 1
    for cg in ["notyettreated", "nevertreated"]:
        mine = cs.att_gt(d, "sdg131_total", "id", "year", "g", control_group=cg, n_boot=9)
        ref = csdid.ATTgt(yname="sdg131_total", tname="year", idname="id", gname="g", data=d,
                          control_group=cg).fit(est_method="reg").results
        ref = pd.DataFrame({"cohort": ref["group"], "time": ref["year"], "ref": ref["att"]})
        m = mine.attgt.merge(ref, on=["cohort", "time"])
        assert len(m) == len(mine.attgt)
        assert np.abs(m["att"] - m["ref"]).max() < 1e-8


def test_outcome_regression_matches_drdid_cell():
    reg = pytest.importorskip("drdid.reg_did")
    d = make_synthetic(n_countries=150, sdg_missing=0.0, covariate_trend=0.8, seed=9)["country_year"]
    r = cs.att_gt(d, "sdg131_total", "iso3", "year", "cohort_annual", covariates=["log_gdppc_2014"], n_boot=9)
    w = d.pivot(index="iso3", columns="year", values="sdg131_total")
    G = d.groupby("iso3")["cohort_annual"].first().fillna(np.inf)
    X = d.groupby("iso3")["log_gdppc_2014"].first()
    g, t, b = 2017, 2019, 2016
    tr, ct = G == g, (G > t) & (G != g)
    keep = tr | ct
    ref = reg.reg_did_panel(w[t][keep], w[b][keep], tr[keep].astype(int), covariates=X[keep].to_numpy()[:, None])
    ref = ref[0] if isinstance(ref, (tuple, list)) else ref
    mine = r.attgt.query("cohort == @g and time == @t")["att"].iloc[0]
    assert mine == pytest.approx(float(ref), abs=1e-8)
