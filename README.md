# Identified, Yet Excluded? Digital ID and social protection coverage

Cross-country evidence on whether the rollout of digital foundational identification systems is
associated with changes in effective social protection coverage in low- and middle-income
countries, for whom, and under which rights safeguards.

- **Design:** staggered adoption difference-in-differences. Country-year panel 2014-2024 (SDG 1.3.1)
  and country-wave panel (Global Findex 2014, 2017, 2021, 2024).
- **Treatment:** an original, hand-coded dataset of the year each country began nationwide
  enrolment in a digital foundational ID, with system design features.
- **Main estimator:** Callaway and Sant'Anna (2021) group-time ATTs with not-yet-treated
  controls and baseline covariates (outcome regression), with country-cluster bootstrap inference.
- **Comparisons and sensitivity:** Sun and Abraham (2021), de Chaisemartin and
  D'Haultfoeuille (2020) DID_M, two-way fixed effects with negative-weight diagnostics, wild
  cluster bootstrap, placebo outcomes, and Rambachan and Roth (2023) bounds.

The analysis plan is in [`docs/analysis_plan.md`](docs/analysis_plan.md) (in Vietnamese) and the
proposal in [`docs/proposal.md`](docs/proposal.md).

## Status

The code is complete and tested on synthetic data. It has **not yet been run on real data**:
the rollout dataset is still to be coded (`data/rollout/`), and the source files are still to
be downloaded (`docs/data_sources.md`). Any output produced with `--synthetic` is labelled
SYNTHETIC and must not be cited.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,crosscheck]"
pytest
python -m idsp.pipeline --synthetic --n-boot 199
```

Real data:

```bash
python -m idsp.data.worldbank      # WDI and WGI through the World Bank API
# download the manual sources into data/raw/manual/ (docs/data_sources.md)
python -m idsp.coding validate     # check the hand-coded rollout dataset
python -m idsp.data.panel          # build data/processed/
python -m idsp.pipeline            # estimates, tables, figures
Rscript r/honestdid.R              # Rambachan-Roth sensitivity (R, HonestDiD)
```

## Repository layout

```
config/            settings.yaml (analysis choices), sources.yaml (indicators and file schemas)
data/rollout/      hand-coded rollout and data-protection-law datasets (tracked)
data/raw, processed/   downloaded and derived data (not tracked)
docs/              proposal, analysis plan, coding protocol, codebook, data sources, review notes
src/idsp/          estimators/, data/, report/, pipeline.py, synthetic.py, coding.py
r/honestdid.R      Rambachan-Roth sensitivity analysis
tests/             unit tests, including cross-checks against csdid and drdid
output/            tables, figures, HonestDiD inputs (not tracked)
```

## Validation of the estimator

`tests/test_estimators.py` checks the following.

- **Recovery of known effects.** The estimators recover the group-time effects in synthetic data.
- **Agreement with reference packages.** Unconditional ATT(g,t) estimates match the `csdid`
  package (a port of R `did`) to machine precision for both control groups. Outcome-regression
  estimates match `drdid.reg_did_panel` cell by cell.
- **Agreement between estimators.** DID_M equals the cohort-size-weighted instantaneous
  Callaway-Sant'Anna effect in a balanced panel.
- **Wild cluster bootstrap.** It has the expected size and power.

## Licence

To be decided by the authors. A suggestion: MIT for the code, and CC BY 4.0 for the hand-coded
rollout dataset. Third-party data keep their own licences (World Bank and ILO: CC BY 4.0;
V-Dem: CC BY-SA 4.0).
