import numpy as np
import pandas as pd
import pytest

from idsp import coding, gaps, safeguards, treatment
from idsp.synthetic import make_synthetic


def test_wave_cohort_lag_rule():
    waves = (2014, 2017, 2021, 2024)
    assert treatment.wave_cohort(2016, waves, 1) == 2017
    assert treatment.wave_cohort(2017, waves, 1) == 2021  # same-year rollout not counted at that wave
    assert treatment.wave_cohort(2017, waves, 0) == 2017
    assert treatment.wave_cohort(2010, waves, 1) == 2014  # always treated at baseline
    assert np.isnan(treatment.wave_cohort(2024, waves, 1))
    assert np.isnan(treatment.wave_cohort(np.nan, waves, 1))


def test_cohort_table_labels():
    c = pd.DataFrame({"g": [2010, 2016, 2016, np.nan, 2030]})
    t = treatment.cohort_table(c, "g", 2014, 2024)
    d = dict(zip(t["cohort"], t["n_countries"]))
    assert d["2016"] == 2 and d["never treated in window"] == 2 and d["always treated (dropped)"] == 1


def test_gaps_sign_convention():
    df = pd.DataFrame({"transfer_male": [30.0], "transfer_female": [25.0]})
    assert gaps.add_gaps(df)["gap_sex"].iloc[0] == 5.0


def test_safeguard_index_split():
    c = make_synthetic(n_countries=100, seed=2)["countries"]
    s = safeguards.safeguard_index(c, ["wgi_va_2014", "wgi_rl_2014", "vdem_cspart_2014"], 2014)
    assert s["high_safeguard"].mean() == pytest.approx(0.5, abs=0.02)
    assert np.corrcoef(s["safeguard"], c["safeguard_true"])[0, 1] > 0.6


def _row(iso3, coder, year, event="national enrolment", status="final", s2="https://b.example"):
    return dict(iso3=iso3, country=iso3, coder=coder, digital_id_system="X", rollout_year=year,
                rollout_event=event, source1_citation="a", source1_url="https://a.example",
                source2_citation="b", source2_url=s2, status=status)


def test_validate_rollout_flags_single_source_and_range():
    df = pd.DataFrame([_row("AAA", "c1", 2015), _row("BBB", "c1", 2015, s2=""),
                       _row("CCC", "c1", 1980), _row("DDD", "c1", np.nan, event="none")])
    p = coding.validate_rollout(df)
    assert set(p["iso3"]) == {"BBB", "CCC"}


def test_agreement_statistics():
    a = pd.DataFrame([_row(c, "c1", y) for c, y in [("A", 2015), ("B", 2016), ("C", 2018), ("D", 2020)]])
    b = pd.DataFrame([_row(c, "c2", y) for c, y in [("A", 2015), ("B", 2017), ("C", 2018), ("D", 2023)]])
    summary, dis = coding.agreement(a, b)
    v = dict(zip(summary["statistic"], summary["value"]))
    assert v["exact rollout-year agreement"] == 0.5
    assert v["agreement within one year"] == 0.75
    assert set(dis["iso3"]) == {"B", "D"}


def test_cohen_kappa_known_value():
    a = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
    b = [1, 0, 0, 0, 1, 0, 1, 1, 1, 1]
    # po = 0.8; pe = 0.6*0.6 + 0.4*0.4 = 0.52; kappa = 0.28/0.48
    assert coding.cohen_kappa(a, b) == pytest.approx(0.28 / 0.48)


def test_second_coder_sample_reproducible():
    iso = [f"C{i}" for i in range(50)]
    s1 = coding.second_coder_sample(iso, 0.2, seed=1)
    assert s1 == coding.second_coder_sample(iso, 0.2, seed=1) and len(s1) == 10
