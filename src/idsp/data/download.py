"""Download the third-party sources and convert them to the tidy files read by `idsp.data.panel`.

Covariates (safe to run while the rollout years are being coded):
- worldbank: WDI and WGI through the World Bank API -> data/raw/wb_<name>.csv
- income_classification: World Bank OGHIST.xlsx -> data/raw/manual/income_classification.csv
- vdem: V-Dem Country-Year Core -> data/raw/manual/vdem.csv

Outcomes (only with --outcomes; CLAUDE.md rule 3 and docs/review_notes.md D1):
- sdg131: ILOSTAT SDG 1.3.1 -> data/raw/manual/sdg131.csv
- findex: Global Findex country-level database, downloaded by hand -> data/raw/manual/findex_transfers.csv

Original files are kept in data/raw/original/ with their retrieval date and listed in MANIFEST.csv.
A file saved there by hand (matching the source's file pattern) is used instead of downloading.
Outcome values are never printed: only row and country counts.

Usage:
    python -m idsp.data.download                    # covariates
    python -m idsp.data.download --outcomes         # covariates and outcomes
    python -m idsp.data.download --only vdem        # one source
    python -m idsp.data.download --refresh          # download again even if a file exists
    python -m idsp.data.download --findex-columns   # list Findex columns to fill config/sources.yaml
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import re
import subprocess
import sys
import time
import zipfile
import zlib
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests

from .. import config
from . import worldbank

ORIGINAL = config.RAW / "original"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; idsp-data-download)"}
INCOME_CODES = {"L", "LM", "UM", "H"}
ILOSTAT_FIELDS = {"ref_area", "sex", "classif1", "time", "obs_value"}
VDEM_COLS = ["country_text_id", "year", "v2x_cspart", "v2csreprss"]
FIRST_YEAR = 2005  # earliest year kept from V-Dem (same window as the World Bank API request)

COVARIATES = ["worldbank", "income_classification", "vdem"]
OUTCOMES = ["sdg131", "findex"]

MANUAL_HELP = {
    "income_classification": (
        "By hand: open https://datahelpdesk.worldbank.org/knowledgebase/articles/906519, download the\n"
        "historical classification by income (OGHIST.xlsx) and save it in data/raw/original/."),
    "vdem": (
        "By hand: open https://v-dem.net/data/the-v-dem-dataset/, download 'Country-Year: V-Dem Core'\n"
        "(CSV, .zip) and save the .zip in data/raw/original/ without renaming it."),
    "sdg131": (
        "By hand: open https://ilostat.ilo.org/data/bulk/, folder INDICATOR, download\n"
        "SDG_0131_SEX_SOC_RT_A.csv.gz and save it in data/raw/original/."),
    "findex": (
        "By hand: open https://www.worldbank.org/en/publication/globalfindex/download-data, download the\n"
        "country-level database (Excel) and save it in data/raw/original/ (the file name must contain\n"
        "'findex'). Then run `python -m idsp.data.download --findex-columns`."),
    "sp_spending": (
        "Optional (extended-covariate robustness check only). ILO World Social Protection Database:\n"
        "public social protection expenditure excluding health, % of GDP. Save it by hand as\n"
        "data/raw/manual/sp_spending.csv with columns iso3, year, sp_spending."),
    "id4d": (
        "Optional, not read by the pipeline (first-stage check, review_notes B4). World Bank ID4D\n"
        "Global Dataset, saved as data/raw/manual/id4d.csv with columns iso3, year, id_ownership."),
}


class SourceError(RuntimeError):
    """A source could not be obtained or converted; the message says what to do."""


# --- files and downloads -------------------------------------------------------------------------

def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(config.ROOT))
    except ValueError:
        return str(p)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(source: str, path: Path, url: str, retrieved: str | None = None) -> None:
    """Append one line to data/raw/original/MANIFEST.csv (once per file)."""
    m = ORIGINAL / "MANIFEST.csv"
    if m.exists() and path.name in set(pd.read_csv(m)["file"]):
        return
    row = dict(source=source, file=path.name, url=url, retrieved=retrieved or dt.date.today().isoformat(),
               bytes=path.stat().st_size, sha256=_sha256(path))
    pd.DataFrame([row]).to_csv(m, mode="a", header=not m.exists(), index=False)


def find_original(patterns: list[str]) -> Path | None:
    """Most recent file in data/raw/original/ whose name matches a pattern (case-insensitive)."""
    if not ORIGINAL.exists():
        return None
    files = [p for p in ORIGINAL.iterdir() if p.is_file() and not p.name.endswith(".part")
             and any(fnmatch.fnmatch(p.name.lower(), pat.lower()) for pat in patterns)]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def head_text(first: bytes) -> str:
    """Start of a downloaded file as text, decompressing gzip if needed."""
    if first[:2] == b"\x1f\x8b":
        try:
            first = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(first, 1 << 14)
        except zlib.error:
            return ""
    return first[: 1 << 14].decode("utf-8-sig", errors="replace")


def zip_check(suffix: str):
    """Accept zip containers (.zip, .xlsx); an HTML error page is rejected."""
    return lambda first: suffix if first[:2] == b"PK" else None


def ilostat_check(first: bytes) -> str | None:
    """Accept an ILOSTAT csv or csv.gz whose header has the code columns."""
    lines = head_text(first).splitlines()
    fields = {f.strip().strip('"') for f in lines[0].split(",")} if lines else set()
    if ILOSTAT_FIELDS <= fields:
        return ".csv.gz" if first[:2] == b"\x1f\x8b" else ".csv"
    return None


def download(urls: list[str], check, source: str, stem: str | None = None, session=None,
             retries: int = 3) -> Path:
    """Try each URL in turn and keep the first response accepted by `check`.

    `check(first_bytes)` returns the file suffix, or None to reject the content (for example an
    HTML page served with status 200). The file is saved as data/raw/original/<stem>_<date><suffix>.
    """
    s = session or requests.Session()
    ORIGINAL.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in urls:
        for attempt in range(retries):
            try:
                print(f"  downloading {url}" + (f" (attempt {attempt + 1})" if attempt else ""))
                with s.get(url, headers=HEADERS, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    chunks = r.iter_content(1 << 20)
                    first = b""
                    for c in chunks:
                        first += c
                        if len(first) >= 1 << 16:
                            break
                    suffix = check(first)
                    if suffix is None:
                        raise ValueError("unexpected content (an HTML page or an error message?)")
                    name = stem or Path(urlparse(url).path).name.split(".")[0]
                    dest = ORIGINAL / f"{name}_{dt.date.today().isoformat()}{suffix}"
                    tmp = dest.with_name(dest.name + ".part")
                    with open(tmp, "wb") as f:
                        f.write(first)
                        for c in chunks:
                            f.write(c)
                    tmp.replace(dest)
                record(source, dest, url)
                print(f"  saved {_rel(dest)} ({dest.stat().st_size / 1e6:.1f} MB)")
                return dest
            except ValueError as e:  # wrong content: the same URL will not do better
                errors.append(f"{url}: {e}")
                break
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code < 500:  # 404 and the like: next URL
                    errors.append(f"{url}: {e}")
                    break
                if attempt == retries - 1:
                    errors.append(f"{url}: {e}")
                else:
                    time.sleep(2 ** (attempt + 1))
            except requests.RequestException as e:
                if attempt == retries - 1:
                    errors.append(f"{url}: {e}")
                else:
                    time.sleep(2 ** (attempt + 1))
    raise SourceError("download failed:\n    " + "\n    ".join(errors))


def obtain(source: str, patterns: list[str], urls: list[str], check, stem: str | None = None,
           refresh: bool = False, session=None) -> Path:
    """Use the file already in data/raw/original/, or download it."""
    existing = find_original(patterns)
    if existing is not None and not refresh:
        print(f"  using {_rel(existing)} (pass --refresh to download again)")
        mtime = dt.date.fromtimestamp(existing.stat().st_mtime).isoformat()
        record(source, existing, "saved by hand or earlier run", retrieved=mtime)
        return existing
    try:
        return download(urls, check, source, stem=stem, session=session)
    except SourceError as e:
        if existing is not None:
            print(f"  WARNING: {e}\n  keeping {_rel(existing)}")
            return existing
        raise SourceError(f"{e}\n{MANUAL_HELP[source]}") from None


def write_manual(df: pd.DataFrame, spec: dict, outcome: bool = False) -> Path:
    config.MANUAL.mkdir(parents=True, exist_ok=True)
    path = config.MANUAL / spec["file"]
    df.to_csv(path, index=False)
    time_col = "wave" if "wave" in df.columns else "year" if "year" in df.columns else None
    span = f", {time_col} {int(df[time_col].min())}-{int(df[time_col].max())}" if time_col and len(df) else ""
    print(f"  wrote {_rel(path)}: rows={len(df)} countries={df['iso3'].nunique()}{span}"
          + (" (values not shown: outcome data)" if outcome else ""))
    return path


# --- parsers -------------------------------------------------------------------------------------

def fiscal_year(label) -> int | None:
    """'FY15' -> 2015, 'FY89' -> 1989, 'FY2015' -> 2015; anything else -> None."""
    m = re.fullmatch(r"FY\s*'?(\d{2}|\d{4})", str(label).strip(), flags=re.I)
    if not m:
        return None
    y = int(m.group(1))
    return y if y >= 100 else (1900 + y if y >= 50 else 2000 + y)


def parse_oghist(path: Path, fy: int) -> pd.DataFrame:
    """iso3, country, income_group for fiscal year `fy` from OGHIST.xlsx.

    Codes are kept as published (L, LM, UM, H). '..' becomes missing. Other codes (for example
    with a footnote star) are kept and reported by the caller.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
    for name in sorted(sheets, key=lambda n: "analytical" not in n.lower()):
        raw = sheets[name]
        for i in range(min(len(raw), 40)):
            years = [fiscal_year(v) for v in raw.iloc[i]]
            if sum(y is not None for y in years) < 5 or fy not in years:
                continue
            col = years.index(fy)
            body = raw.iloc[i + 1:]
            iso = body.apply(lambda c: c.astype(str).str.strip().str.fullmatch(r"[A-Z]{3}", na=False).sum())
            code_col = int(np.argmax(iso.to_numpy()[:col]))
            rows = body[body[code_col].astype(str).str.strip().str.fullmatch(r"[A-Z]{3}", na=False)]
            group = rows[col].astype(str).str.strip().replace({"..": np.nan, "nan": np.nan, "": np.nan})
            out = pd.DataFrame({"iso3": rows[code_col].astype(str).str.strip(),
                                "country": rows[code_col + 1].astype(str).str.strip(),
                                "income_group": group})
            known = out["income_group"].dropna().str.rstrip("*").isin(INCOME_CODES)
            if len(known) and known.mean() >= 0.5:
                return out.reset_index(drop=True)
    raise ValueError(f"No sheet in {path.name} has income codes under a FY{fy % 100:02d} header.")


def parse_wb_countries(payload) -> pd.DataFrame:
    """iso3 and region from the World Bank API country list (aggregates dropped)."""
    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise RuntimeError("Unexpected World Bank API response for the country list.")
    rows = [(r["id"], (r.get("region") or {}).get("value", "").strip()) for r in payload[1]]
    df = pd.DataFrame(rows, columns=["iso3", "region"])
    return df[(df["region"] != "") & (df["region"] != "Aggregates")].reset_index(drop=True)


def fetch_regions(base_url: str, session=None) -> pd.DataFrame:
    s = session or requests.Session()
    r = s.get(f"{base_url}/country", params={"format": "json", "per_page": 500}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return parse_wb_countries(r.json())


def parse_vdem(path: Path, first_year: int = FIRST_YEAR) -> pd.DataFrame:
    """iso3, year, v2x_cspart, v2csreprss from the V-Dem Country-Year file (.zip or .csv)."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.infolist() if m.filename.lower().endswith(".csv")
                       and "__macosx" not in m.filename.lower()]
            if not members:
                raise ValueError(f"{path.name} has no .csv file.")
            with zf.open(max(members, key=lambda m: m.file_size)) as f:
                df = pd.read_csv(f, usecols=VDEM_COLS)
    else:
        df = pd.read_csv(path, usecols=VDEM_COLS)
    df = df[df["year"] >= first_year].rename(columns={"country_text_id": "iso3"})
    return df[["iso3", "year", "v2x_cspart", "v2csreprss"]].reset_index(drop=True)


def parse_ilostat(path: Path, sex: str, classif1: str) -> pd.DataFrame:
    """iso3, year, sdg131_total (+ source and status columns, kept for review_notes B1)."""
    df = pd.read_csv(path, dtype=str, low_memory=False)
    missing = ILOSTAT_FIELDS - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {sorted(missing)}.")
    available = sorted(df["classif1"].dropna().unique())
    if classif1 not in available:
        raise ValueError(f"classif1 '{classif1}' is not in {path.name}. Available: {available}. "
                         "Set manual.sdg131.classif1 in config/sources.yaml (VERIFY).")
    d = df[(df["sex"] == sex) & (df["classif1"] == classif1) & df["ref_area"].str.fullmatch(r"[A-Z]{3}", na=False)]
    out = pd.DataFrame({"iso3": d["ref_area"],
                        "year": pd.to_numeric(d["time"].str[:4], errors="coerce"),
                        "sdg131_total": pd.to_numeric(d["obs_value"], errors="coerce"),
                        "sdg131_source": d.get("source"),
                        "sdg131_obs_status": d.get("obs_status")}).dropna(subset=["year", "sdg131_total"])
    out["year"] = out["year"].astype(int)
    dup = out[out.duplicated(["iso3", "year"], keep=False)]
    if len(dup):
        raise ValueError(f"{len(dup)} rows share a country-year (several sources?): "
                         f"{sorted(dup['iso3'].unique())}. Decide a rule, log it in docs/deviations.md, "
                         "then convert by hand.")
    return out.sort_values(["iso3", "year"]).reset_index(drop=True)


CODE_RE = r"(country|economy)[ _]?(code|iso3?)|iso3?|code"


def _match_col(columns, pattern: str) -> str | None:
    hits = [c for c in columns if re.fullmatch(pattern, str(c).strip(), flags=re.I)]
    return hits[0] if hits else None


def read_table(path: Path, sheet: str | None = None) -> pd.DataFrame:
    """Read a csv or the data sheet of an xlsx, finding the header row (the one with a country code)."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    heads = pd.read_excel(path, sheet_name=sheet if sheet else None, header=None, nrows=30)
    if isinstance(heads, pd.DataFrame):
        heads = {sheet: heads}
    best = None
    for name, h in heads.items():
        for i in range(len(h)):
            row = h.iloc[i].dropna()
            if _match_col(row.tolist(), CODE_RE) is not None:
                if best is None or len(row) > best[2]:
                    best = (name, i, len(row))
                break
    if best is None:
        raise ValueError(f"No sheet in {path.name} has a country-code header.")
    return pd.read_excel(path, sheet_name=best[0], header=best[1])


def findex_columns(df: pd.DataFrame, spec: dict) -> str:
    """Text report of the Findex file layout: id columns, groups and candidate transfer columns."""
    country = spec.get("country_col") or _match_col(df.columns, CODE_RE)
    year = spec.get("year_col") or _match_col(df.columns, r"year|wave|survey year")
    lines = [f"rows={len(df)} columns={df.shape[1]}", f"country column: {country}", f"year column: {year}"]
    if year is not None:
        lines.append(f"years: {df[year].value_counts().sort_index().to_dict()}")
    for c in df.columns:
        text = pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])
        if text and df[c].astype(str).str.fullmatch(r"(?i)female|women", na=False).any():
            lines.append(f"possible group column (long layout): {c!r} values {sorted(df[c].dropna().astype(str).unique())[:40]}")
    lines.append("candidate transfer columns:")
    pat = re.compile(r"govern|transfer|pension|wage|payment|benefit|fin3\d|fin4\d", re.I)
    lines += [f"  {c!r}" for c in df.columns if pat.search(str(c))]
    return "\n".join(lines)


def convert_findex(df: pd.DataFrame, spec: dict, targets: list[str]) -> pd.DataFrame:
    """Tidy iso3, wave, transfer_* from the Findex database, following the mapping in config."""
    series = spec.get("series") or {}
    if not series.get("transfer_total"):
        raise SourceError("manual.findex.series in config/sources.yaml is not filled in. Run\n"
                          "`python -m idsp.data.download --findex-columns`, choose the column for each\n"
                          "group, and record the question wave by wave in docs/codebook.md (review_notes B2).")
    country = spec.get("country_col") or _match_col(df.columns, CODE_RE)
    year = spec.get("year_col") or _match_col(df.columns, r"year|wave|survey year")
    group_col = spec.get("group_col")
    if country is None or year is None:
        raise SourceError("Country or year column not found; set country_col and year_col in config.")
    long = []
    for t in targets:
        m = series.get(t)
        if not m:
            continue
        col, grp = (m, None) if isinstance(m, str) else (m[0], m[1])
        if col not in df.columns:
            raise SourceError(f"Findex column {col!r} (for {t}) not in the file.")
        d = df if grp is None else df[df[group_col].astype(str) == str(grp)]
        d = d[d[country].astype(str).str.strip().str.fullmatch(r"[A-Z]{3}", na=False)]
        long.append(pd.DataFrame({"iso3": d[country].astype(str).str.strip(),
                                  "year": pd.to_numeric(d[year], errors="coerce"),
                                  "target": t, "value": pd.to_numeric(d[col], errors="coerce")}))
    x = pd.concat(long, ignore_index=True).dropna(subset=["year"])
    wave_map = {int(k): int(v) for k, v in spec["wave_map"].items()}
    x["wave"] = x["year"].astype(int).map(wave_map)
    dropped = sorted(x.loc[x["wave"].isna(), "year"].astype(int).unique())
    if dropped:
        print(f"  years not in wave_map, dropped: {dropped}")
    x = x.dropna(subset=["wave"])
    dup = x[x.duplicated(["iso3", "wave", "target"], keep=False)]
    if len(dup):
        raise SourceError(f"Several rows map to the same country-wave: {sorted(dup['iso3'].unique())[:20]}. "
                          "Check wave_map (for example 2021 and 2022 for one country).")
    if x["value"].max() <= 1.0:
        x["value"] *= 100
        print("  values were shares (0-1): converted to percent")
    out = x.pivot_table(index=["iso3", "wave"], columns="target", values="value", aggfunc="first").reset_index()
    for t in targets:
        if t not in out.columns:
            out[t] = np.nan
    out["wave"] = out["wave"].astype(int)
    return out[["iso3", "wave"] + targets].sort_values(["iso3", "wave"]).reset_index(drop=True)


# --- steps ---------------------------------------------------------------------------------------

class Run:
    def __init__(self, refresh: bool):
        self.refresh = refresh
        self.session = requests.Session()
        self.sources = config.load("sources")
        self.settings = config.load("settings")


def step_worldbank(run: Run) -> None:
    src = run.sources["worldbank_api"]
    config.RAW.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, spec in src["indicators"].items():
        path = config.RAW / f"wb_{name}.csv"
        if path.exists() and not run.refresh:
            print(f"  {name}: {_rel(path)} exists")
            continue
        try:
            df = worldbank.fetch(spec["code"], spec["source"], src["date_range"], src["base_url"], session=run.session)
        except Exception as e:  # noqa: BLE001  (report every failing indicator, keep going)
            failed.append(f"{name} ({spec['code']}, source {spec['source']}): {e}")
            continue
        df.to_csv(path, index=False)
        print(f"  {name:15s} {spec['code']:20s} rows={len(df):6d} -> {_rel(path)}")
    if failed:
        raise SourceError("\n".join(failed) + "\nCheck these codes in config/sources.yaml "
                          "(the WGI codes are marked VERIFY) and on DataBank.")


def step_income_classification(run: Run) -> None:
    spec = run.sources["manual"]["income_classification"]
    p = obtain("income_classification", ["oghist*.xlsx"], spec["urls"], zip_check(".xlsx"), stem="OGHIST",
               refresh=run.refresh, session=run.session)
    fy = run.settings["sample"]["income_classification_fy"]
    df = parse_oghist(p, fy)
    try:
        df = df.merge(fetch_regions(run.sources["worldbank_api"]["base_url"], run.session), on="iso3", how="left")
    except Exception as e:  # noqa: BLE001
        print(f"  WARNING: regions not added ({e}); only needed for the leave-one-region-out check.")
        df["region"] = np.nan
    odd = df[df["income_group"].notna() & ~df["income_group"].isin(INCOME_CODES)]
    if len(odd):
        print(f"  NOTE: FY{fy} codes outside L/LM/UM/H kept as published: "
              f"{dict(zip(odd['iso3'], odd['income_group']))}. These countries are outside the sample "
              "unless a change is logged in docs/deviations.md.")
    write_manual(df[spec["schema"]], spec)


def step_vdem(run: Run) -> None:
    spec = run.sources["manual"]["vdem"]
    p = obtain("vdem", ["v-dem-cy*.zip", "v-dem-cy*.csv"], spec["urls"], zip_check(".zip"),
               refresh=run.refresh, session=run.session)
    print("  reading V-Dem (large file, this can take a minute)")
    write_manual(parse_vdem(p)[spec["schema"]], spec)


def step_sdg131(run: Run) -> None:
    spec = run.sources["manual"]["sdg131"]
    ind = spec["ilostat_id"]
    p = obtain("sdg131", [f"{ind.lower()}*.csv*"], [u.format(id=ind) for u in spec["urls"]], ilostat_check,
               stem=ind, refresh=run.refresh, session=run.session)
    df = parse_ilostat(p, spec["sex"], spec["classif1"])
    write_manual(df[spec["schema"] + ["sdg131_source", "sdg131_obs_status"]], spec, outcome=True)


def _findex_file(spec: dict) -> Path:
    p = find_original(spec["original_pattern"])
    if p is None:
        raise SourceError(f"No Findex file in data/raw/original/.\n{MANUAL_HELP['findex']}")
    record("findex", p, "saved by hand", retrieved=dt.date.fromtimestamp(p.stat().st_mtime).isoformat())
    return p


def step_findex(run: Run) -> None:
    spec = run.sources["manual"]["findex"]
    p = _findex_file(spec)
    print(f"  using {_rel(p)}")
    targets = [c for c in spec["schema"] if c not in ("iso3", "wave")]
    df = convert_findex(read_table(p, spec.get("sheet")), spec, targets)
    empty = [t for t in targets if df[t].isna().all()]
    if empty:
        print(f"  NOTE: no data for {empty}. If rural/urban are missing, gap_residence leaves the H2 "
              "family: log it in docs/deviations.md before running (review_notes B3).")
    write_manual(df, spec, outcome=True)


STEPS = {"worldbank": step_worldbank, "income_classification": step_income_classification,
         "vdem": step_vdem, "sdg131": step_sdg131, "findex": step_findex}


def coding_frozen() -> bool | None:
    """True if the git tag `coding-freeze` exists; None if git is unavailable."""
    try:
        r = subprocess.run(["git", "tag", "-l", "coding-freeze"], cwd=config.ROOT, capture_output=True,
                           text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return bool(r.stdout.strip()) if r.returncode == 0 else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m idsp.data.download", description=__doc__.split("\n\n")[0])
    ap.add_argument("--outcomes", action="store_true", help="also obtain the outcome data (SDG 1.3.1, Findex)")
    ap.add_argument("--only", nargs="+", choices=list(STEPS), help="run only these sources")
    ap.add_argument("--refresh", action="store_true", help="download again even if a file exists")
    ap.add_argument("--findex-columns", action="store_true", help="list the Findex file layout and exit")
    args = ap.parse_args(argv)

    if args.findex_columns:
        spec = config.load("sources")["manual"]["findex"]
        try:
            p = _findex_file(spec)
        except SourceError as e:
            print(e)
            return 1
        report = findex_columns(read_table(p, spec.get("sheet")), spec)
        out = ORIGINAL / "findex_columns.txt"
        out.write_text(report + "\n", encoding="utf-8")
        print(f"{_rel(p)}\n{report}\n\n(saved to {_rel(out)}; fill manual.findex in config/sources.yaml)")
        return 0

    steps = args.only or COVARIATES + (OUTCOMES if args.outcomes else [])
    if any(s in OUTCOMES for s in steps):
        if not args.outcomes:
            ap.error("sdg131 and findex are outcome data: add --outcomes (see CLAUDE.md rule 3).")
        if coding_frozen() is False:
            print("WARNING: no git tag `coding-freeze` yet. Do not open the outcome files while rollout years\n"
                  "are being coded (CLAUDE.md rule 3), and register on OSF before merging outcomes with\n"
                  "rollout years (review_notes D1).\n")

    run = Run(args.refresh)
    status = {}
    for name in steps:
        print(f"[{name}]")
        try:
            STEPS[name](run)
            status[name] = "ok"
        except Exception as e:  # noqa: BLE001  (report and go on to the next source)
            print(f"  FAILED: {e}" if isinstance(e, SourceError) else f"  FAILED: {type(e).__name__}: {e}")
            status[name] = "FAILED"

    print("\nSummary")
    for name, st in status.items():
        print(f"  {name:22s} {st}")
    if not args.outcomes:
        print(f"  {'sdg131, findex':22s} not run (outcomes: add --outcomes)")
    for name in ["sp_spending", "id4d"]:
        f = config.MANUAL / run.sources["manual"][name]["file"]
        if not f.exists():
            print(f"\n[{name}] {MANUAL_HELP[name]}")
    print("\nHand-coded files (data/rollout/) cannot be downloaded: see docs/coding_protocol.md.")
    return 1 if "FAILED" in status.values() else 0


if __name__ == "__main__":
    sys.exit(main())
