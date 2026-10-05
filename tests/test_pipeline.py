import pandas as pd
import pytest

from idsp import config, pipeline
from idsp.data import worldbank


def test_pipeline_runs_on_synthetic_data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    res = pipeline.run(synthetic=True, n_boot=49)
    assert {"H1", "H2", "H3", "H1 robustness", "Placebo"} <= set(res["analysis"])
    main = res[(res["analysis"] == "H1") & (res["outcome"] == "sdg131_total")].iloc[0]
    assert main["ci_low"] > 0  # the synthetic DGP has a positive effect
    t = pd.read_csv(tmp_path / "tables" / "results_overall.csv")
    assert (t["data"] == "SYNTHETIC").all()
    assert (tmp_path / "honestdid" / "H1_sdg131_total.json").exists()


def test_worldbank_page_parser():
    payload = [{"page": 1, "pages": 2, "per_page": 2, "total": 3},
               [{"countryiso3code": "VNM", "date": "2015", "value": 1.5, "indicator": {"id": "X"}},
                {"countryiso3code": "", "date": "2015", "value": 2.0, "indicator": {"id": "X"}}]]
    recs, pages = worldbank.parse_page(payload)
    assert pages == 2 and recs[0] == {"iso3": "VNM", "year": 2015, "value": 1.5}
    with pytest.raises(RuntimeError):
        worldbank.parse_page([{"message": [{"key": "Invalid value"}]}])
