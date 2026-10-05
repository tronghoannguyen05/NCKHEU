"""Fetch World Bank indicators (WDI, WGI) through the public API v2.

Writes data/raw/wb_<name>.csv with columns iso3, year, value. Aggregates (regions, income
groups) are kept in the raw file and dropped later by the join on the country list.

Usage: python -m idsp.data.worldbank [name ...]
"""

from __future__ import annotations

import sys
import time

import pandas as pd
import requests

from .. import config


def parse_page(payload) -> tuple[list[dict], int]:
    """Parse one API response page: returns (records, number of pages)."""
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        msg = payload[0].get("message") if isinstance(payload, list) and payload else payload
        raise RuntimeError(f"Unexpected World Bank API response: {msg}")
    meta, rows = payload
    recs = [{"iso3": r.get("countryiso3code") or None, "year": int(r["date"]), "value": r["value"]}
            for r in rows if r.get("date", "").isdigit()]
    return recs, int(meta.get("pages", 1))


def fetch(code: str, source: int, date_range: str, base_url: str, session=None, retries=4) -> pd.DataFrame:
    s = session or requests.Session()
    url = f"{base_url}/country/all/indicator/{code}"
    out, page, pages = [], 1, 1
    while page <= pages:
        params = {"format": "json", "per_page": 20000, "date": date_range, "source": source, "page": page}
        for attempt in range(retries):
            try:
                r = s.get(url, params=params, timeout=60)
                r.raise_for_status()
                recs, pages = parse_page(r.json())
                break
            except (requests.RequestException, ValueError):
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** (attempt + 1))
        out.extend(recs)
        page += 1
    df = pd.DataFrame(out, columns=["iso3", "year", "value"]).dropna(subset=["iso3"])
    return df[df["iso3"].str.len() == 3]


def main(names=None):
    src = config.load("sources")["worldbank_api"]
    config.RAW.mkdir(parents=True, exist_ok=True)
    for name, spec in src["indicators"].items():
        if names and name not in names:
            continue
        df = fetch(spec["code"], spec["source"], src["date_range"], src["base_url"])
        path = config.RAW / f"wb_{name}.csv"
        df.to_csv(path, index=False)
        print(f"{name:15s} {spec['code']:20s} rows={len(df):6d} -> {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
