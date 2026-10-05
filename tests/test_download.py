"""Parsers and download logic of idsp.data.download, on small hand-made files (no network)."""

import gzip
import zipfile

import numpy as np
import pandas as pd
import pytest
import requests

from idsp.data import download as D


def test_fiscal_year_labels():
    assert D.fiscal_year("FY15") == 2015
    assert D.fiscal_year("FY89") == 1989
    assert D.fiscal_year("FY2015") == 2015
    assert D.fiscal_year("Data for calendar year :") is None


def _oghist(path):
    lending = pd.DataFrame([[None, None, "FY13", "FY14", "FY15", "FY16", "FY17"],
                            ["AFG", "Afghanistan", "IDA", "IDA", "IDA", "IDA", "IDA"]])
    analytical = pd.DataFrame([
        ["World Bank Analytical Classifications", None, None, None, None, None, None],
        [None, None, None, None, None, None, None],
        [None, None, "FY13", "FY14", "FY15", "FY16", "FY17"],
        [None, "Data for calendar year :", 2011, 2012, 2013, 2014, 2015],
        ["AFG", "Afghanistan", "L", "L", "L", "L", "L"],
        ["VNM", "Viet Nam", "LM", "LM", "LM", "LM", "LM"],
        [None, None, None, None, None, None, None],
        ["YEM", "Yemen, Rep.", "LM", "LM", "LM*", "LM", "L"],
        ["BRA", "Brazil", "UM", "UM", "UM", "UM", "UM"],
        ["SSD", "South Sudan", "..", "..", "..", "L", "L"],
        ["Note: ...", None, None, None, None, None, None]])
    with pd.ExcelWriter(path) as w:
        lending.to_excel(w, sheet_name="Operational History", header=False, index=False)
        analytical.to_excel(w, sheet_name="Country Analytical History", header=False, index=False)


def test_parse_oghist_reads_fy_column(tmp_path):
    _oghist(tmp_path / "OGHIST.xlsx")
    df = D.parse_oghist(tmp_path / "OGHIST.xlsx", 2015).set_index("iso3")
    assert list(df.index) == ["AFG", "VNM", "YEM", "BRA", "SSD"]
    assert df.loc["VNM", "income_group"] == "LM" and df.loc["VNM", "country"] == "Viet Nam"
    assert df.loc["YEM", "income_group"] == "LM*"   # kept as published, reported by the caller
    assert pd.isna(df.loc["SSD", "income_group"])
    with pytest.raises(ValueError):
        D.parse_oghist(tmp_path / "OGHIST.xlsx", 2030)


def test_parse_wb_countries_drops_aggregates():
    payload = [{"pages": 1}, [{"id": "VNM", "region": {"value": "East Asia & Pacific "}},
                              {"id": "EAS", "region": {"value": "Aggregates"}}]]
    df = D.parse_wb_countries(payload)
    assert df.to_dict("records") == [{"iso3": "VNM", "region": "East Asia & Pacific"}]


def test_parse_vdem_zip(tmp_path):
    csv = "country_name,country_text_id,year,v2x_cspart,v2csreprss,v2x_polyarchy\n" \
          "Vietnam,VNM,2000,0.1,-1.0,0.2\nVietnam,VNM,2014,0.2,-1.5,0.2\n"
    p = tmp_path / "V-Dem-CY-Core-v16_csv.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("V-Dem-CY-Core-v16_csv/V-Dem-CY-Core-v16.csv", csv)
        zf.writestr("V-Dem-CY-Core-v16_csv/codebook.pdf", "x")
    df = D.parse_vdem(p)
    assert list(df.columns) == ["iso3", "year", "v2x_cspart", "v2csreprss"]
    assert df.to_dict("records") == [{"iso3": "VNM", "year": 2014, "v2x_cspart": 0.2, "v2csreprss": -1.5}]


ILO_ROWS = [
    ("AFG", "X01:1", "SEX_T", "SOC_CONTIG_TOTAL", "2016", "10.5", ""),
    ("AFG", "X01:1", "SEX_F", "SOC_CONTIG_TOTAL", "2016", "8.0", ""),
    ("AFG", "X01:1", "SEX_T", "SOC_CONTIG_OLD", "2016", "20.0", ""),
    ("VNM", "BA:1", "SEX_T", "SOC_CONTIG_TOTAL", "2020", "38.8", "B"),
    ("X01", "X01:1", "SEX_T", "SOC_CONTIG_TOTAL", "2020", "46.9", ""),
]


def _ilostat(path, rows):
    df = pd.DataFrame(rows, columns=["ref_area", "source", "sex", "classif1", "time", "obs_value", "obs_status"])
    df.insert(2, "indicator", "SDG_0131_SEX_SOC_RT")
    df.to_csv(path, index=False)


def test_parse_ilostat_filters_total(tmp_path):
    p = tmp_path / "SDG_0131_SEX_SOC_RT_A_2026-10-05.csv.gz"
    _ilostat(p, ILO_ROWS)
    df = D.parse_ilostat(p, "SEX_T", "SOC_CONTIG_TOTAL")
    assert list(zip(df["iso3"], df["year"], df["sdg131_total"])) == [("AFG", 2016, 10.5), ("VNM", 2020, 38.8)]
    assert df["sdg131_source"].tolist() == ["X01:1", "BA:1"]
    with pytest.raises(ValueError, match="SOC_CONTIG_OLD"):    # lists the codes that exist
        D.parse_ilostat(p, "SEX_T", "SOC_CONTIG_ALL")


def test_parse_ilostat_refuses_duplicates(tmp_path):
    p = tmp_path / "ilo.csv"
    _ilostat(p, ILO_ROWS + [("VNM", "XA:2", "SEX_T", "SOC_CONTIG_TOTAL", "2020", "37.0", "")])
    with pytest.raises(ValueError, match="VNM"):
        D.parse_ilostat(p, "SEX_T", "SOC_CONTIG_TOTAL")


def test_content_checks():
    header = b"ref_area,source,indicator,sex,classif1,time,obs_value,obs_status\nAFG,..."
    assert D.ilostat_check(header) == ".csv"
    assert D.ilostat_check(gzip.compress(header)) == ".csv.gz"
    assert D.ilostat_check(b"<!DOCTYPE html><html>Not found</html>") is None
    assert D.zip_check(".xlsx")(b"PK\x03\x04...") == ".xlsx"
    assert D.zip_check(".xlsx")(b"<html>") is None


class _Resp:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)

    def iter_content(self, n):
        for i in range(0, len(self.body), 7):
            yield self.body[i:i + 7]


class _Session:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url, **kw):
        self.calls.append(url)
        return self.responses[url]


def test_download_skips_bad_urls_and_records(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "ORIGINAL", tmp_path)
    body = b"PK\x03\x04" + b"x" * 100
    s = _Session({"https://a/OGHIST.xlsx": _Resp(b"", 404),
                  "https://b/OGHIST.xlsx": _Resp(b"<html>moved</html>"),
                  "https://c/OGHIST.xlsx": _Resp(body)})
    p = D.download(list(s.responses), D.zip_check(".xlsx"), "income_classification", stem="OGHIST", session=s)
    assert s.calls == list(s.responses)              # 404 and HTML are not retried
    assert p.name.startswith("OGHIST_") and p.suffix == ".xlsx" and p.read_bytes() == body
    m = pd.read_csv(tmp_path / "MANIFEST.csv")
    assert m["url"].tolist() == ["https://c/OGHIST.xlsx"] and len(m["sha256"].iloc[0]) == 64
    assert D.find_original(["oghist*.xlsx"]) == p
    with pytest.raises(D.SourceError):
        D.download(["https://a/OGHIST.xlsx"], D.zip_check(".xlsx"), "x", session=s)


def _findex_spec(**series):
    return {"wave_map": {2014: 2014, 2017: 2017, 2021: 2021, 2022: 2021, 2024: 2024}, "series": series}


TARGETS = ["transfer_total", "transfer_female", "transfer_male", "transfer_poor40", "transfer_rich60",
           "transfer_rural", "transfer_urban"]


def test_convert_findex_wide_layout():
    df = pd.DataFrame({"Country name": ["Viet Nam"] * 3 + ["Kenya"],
                       "Country code": ["VNM", "VNM", "VNM", "KEN"],
                       "Year": [2011, 2017, 2022, 2017],
                       "Gov transfer": [0.10, 0.20, 0.30, 0.40],
                       "Gov transfer, female": [0.10, 0.25, "..", 0.35]})
    out = D.convert_findex(df, _findex_spec(transfer_total="Gov transfer", transfer_female="Gov transfer, female"),
                           TARGETS)
    assert list(out.columns) == ["iso3", "wave"] + TARGETS
    v = out.set_index(["iso3", "wave"])
    assert v.index.tolist() == [("KEN", 2017), ("VNM", 2017), ("VNM", 2021)]   # 2011 not in wave_map
    assert v.loc[("VNM", 2021), "transfer_total"] == pytest.approx(30.0)      # shares -> percent
    assert np.isnan(v.loc[("VNM", 2021), "transfer_female"]) and v["transfer_rural"].isna().all()


def test_convert_findex_long_layout_and_duplicate_waves():
    df = pd.DataFrame({"Economy code": ["VNM"] * 4, "Year": [2021, 2021, 2024, 2024],
                       "Group": ["All", "Female", "All", "Female"], "fin_gov": [30.0, 28.0, 40.0, 37.0]})
    spec = _findex_spec(transfer_total=["fin_gov", "All"], transfer_female=["fin_gov", "Female"])
    spec["group_col"] = "Group"
    out = D.convert_findex(df, spec, TARGETS).set_index("wave")
    assert out.loc[2024, "transfer_female"] == 37.0 and out.loc[2021, "transfer_total"] == 30.0
    dup = pd.concat([df, df.assign(Year=2022)])
    with pytest.raises(D.SourceError, match="same country-wave"):
        D.convert_findex(dup, spec, TARGETS)
    with pytest.raises(D.SourceError, match="not filled in"):
        D.convert_findex(df, _findex_spec(), TARGETS)
    assert "possible group column (long layout): 'Group'" in D.findex_columns(df, {})


def test_read_table_finds_header_row(tmp_path):
    p = tmp_path / "GlobalFindexDatabase2025.xlsx"
    body = pd.DataFrame([["The Global Findex Database 2025", None, None], [None, None, None],
                         ["Country name", "Country code", "Year"], ["Viet Nam", "VNM", 2024]])
    with pd.ExcelWriter(p) as w:
        pd.DataFrame([["Notes"], ["text"]]).to_excel(w, sheet_name="Notes", header=False, index=False)
        body.to_excel(w, sheet_name="Data", header=False, index=False)
    df = D.read_table(p)
    assert list(df.columns) == ["Country name", "Country code", "Year"] and df["Country code"].tolist() == ["VNM"]
    assert "country column: Country code" in D.findex_columns(df, {})


def test_outcomes_need_flag():
    with pytest.raises(SystemExit):
        D.main(["--only", "sdg131"])
