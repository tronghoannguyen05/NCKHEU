import numpy as np
import pandas as pd

from idsp import config
from idsp.data import panel


def _setup(tmp_path, monkeypatch):
    root = tmp_path
    raw, manual, rollout = root / "data/raw", root / "data/raw/manual", root / "data/rollout"
    for p in (raw, manual, rollout):
        p.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "ROOT", root)
    monkeypatch.setattr(config, "RAW", raw)
    monkeypatch.setattr(config, "MANUAL", manual)
    monkeypatch.setattr(config, "PROCESSED", root / "data/processed")

    iso = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    pd.DataFrame({"iso3": iso + ["HHH"], "country": iso + ["HHH"], "region": "SSA",
                  "income_group": ["L", "LM", "UM", "LM", "L", "H"]}).to_csv(manual / "income_classification.csv", index=False)
    years = range(2008, 2025)
    rng = np.random.default_rng(0)
    for name in ["gdppc_ppp", "urban", "mobile", "battle_deaths", "elec_access", "agri_land", "wgi_va", "wgi_rl"]:
        rows = [(c, y, float(rng.uniform(1, 90))) for c in iso + ["HHH", "WLD"] for y in years]
        pd.DataFrame(rows, columns=["iso3", "year", "value"]).to_csv(raw / f"wb_{name}.csv", index=False)
    pd.DataFrame([(c, y, rng.uniform(10, 60)) for c in iso for y in range(2014, 2025, 2)],
                 columns=["iso3", "year", "sdg131_total"]).to_csv(manual / "sdg131.csv", index=False)
    pd.DataFrame([(c, y, rng.uniform(0, 1), rng.normal()) for c in iso for y in years],
                 columns=["iso3", "year", "v2x_cspart", "v2csreprss"]).to_csv(manual / "vdem.csv", index=False)
    fx = [dict(iso3=c, wave=w, **{k: rng.uniform(5, 50) for k in
          ["transfer_total", "transfer_female", "transfer_male", "transfer_poor40", "transfer_rich60",
           "transfer_rural", "transfer_urban"]}) for c in iso for w in (2014, 2017, 2021, 2024)]
    pd.DataFrame(fx).to_csv(manual / "findex_transfers.csv", index=False)
    roll = pd.read_csv(config.ROLLOUT / "rollout_coding.csv").iloc[0:0]
    recs = []
    for c, y in zip(iso, [2012, 2016, 2019, np.nan, 2023]):
        recs.append(dict(iso3=c, country=c, coder="c1", digital_id_system="X", rollout_year=y,
                         rollout_event="none" if np.isnan(y) else "national enrolment",
                         source1_citation="a", source1_url="https://a", source2_citation="b",
                         source2_url="https://b", status="final", biometric_auth_mandatory_benefits=1))
    pd.concat([roll, pd.DataFrame(recs)]).to_csv(rollout / "rollout_coding.csv", index=False)
    pd.DataFrame({"iso3": iso, "dp_law_year": [2010, np.nan, 2018, 2005, np.nan]}).to_csv(rollout / "dp_law_coding.csv", index=False)


def test_build_panels(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    out = panel.build()
    c = out["countries"]
    assert set(c["iso3"]) == {"AAA", "BBB", "CCC", "DDD", "EEE"}  # high income dropped
    g = dict(zip(c["iso3"], c["cohort_wave"]))
    assert g["BBB"] == 2017 and g["CCC"] == 2021 and g["EEE"] == 2024 and np.isnan(g["DDD"])
    assert c["safeguard"].notna().all() and c["high_safeguard"].isin([0, 1]).all()
    cy, cw = out["country_year"], out["country_wave"]
    assert len(cy) == 5 * 11 and len(cw) == 5 * 4
    assert {"gap_sex", "gap_income", "gap_residence"} <= set(cw.columns)
    assert (tmp_path / "data/processed/panel_country_year.csv").exists()
